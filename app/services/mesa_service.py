"""
mesa_service.py
Async business logic for Mesa and Reserva with state machine enforcement.
Mesa states: disponible → ocupada | reservada → disponible
Reserva states: pendiente → confirmada | cancelada; confirmada → completada | cancelada
"""
import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.mesa import Mesa, Reserva
from app.repositories import mesa_repo
from app.schemas.mesa_schema import (
    MesaCreate,
    MesaUpdate,
    ReservaCreate,
    ReservaUpdate,
)


_MESA_TRANSITIONS: dict[str, set[str]] = {
    "disponible": {"ocupada", "reservada"},
    "ocupada": {"disponible"},
    "reservada": {"ocupada", "disponible"},
}

_RESERVA_TRANSITIONS: dict[str, set[str]] = {
    "pendiente": {"confirmada", "cancelada"},
    "confirmada": {"completada", "cancelada"},
    "completada": set(),
    "cancelada": set(),
}


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _validate_mesa_transition(current: str, next_state: str) -> None:
    allowed = _MESA_TRANSITIONS.get(current, set())
    if next_state not in allowed:
        raise MajesaError(
            f"Transición de mesa inválida: {current!r} → {next_state!r}. "
            f"Permitidas: {sorted(allowed) or 'ninguna'}",
            400,
        )


def _validate_reserva_transition(current: str, next_state: str) -> None:
    allowed = _RESERVA_TRANSITIONS.get(current, set())
    if next_state not in allowed:
        raise MajesaError(
            f"Transición de reserva inválida: {current!r} → {next_state!r}. "
            f"Permitidas: {sorted(allowed) or 'ninguna'}",
            409,
        )


# ── Mesa ──────────────────────────────────────────────────────────────────────

async def get_mesa(db: AsyncSession, id_mesa: int) -> Mesa:
    mesa = await mesa_repo.get_mesa_by_id(db, id_mesa)
    if not mesa:
        raise MajesaError(f"Mesa {id_mesa} no encontrada", 404)
    return mesa


async def get_mesas(
    db: AsyncSession, estado: str | None = None, solo_activas: bool = True
) -> list[Mesa]:
    return await mesa_repo.get_mesas(db, estado=estado, solo_activas=solo_activas)


async def create_mesa(db: AsyncSession, data: MesaCreate) -> Mesa:
    existing = await mesa_repo.get_mesa_by_numero(db, data.numero)
    if existing:
        raise MajesaError(f"Ya existe una mesa con número {data.numero!r}", 409)
    mesa = Mesa(**data.model_dump(), estado="disponible")
    mesa = await mesa_repo.create_mesa(db, mesa)
    await db.commit()
    return mesa


async def update_mesa(db: AsyncSession, id_mesa: int, data: MesaUpdate) -> Mesa:
    mesa = await get_mesa(db, id_mesa)
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No hay campos para actualizar")
    mesa = await mesa_repo.update_mesa(db, mesa, fields)
    await db.commit()
    return mesa


async def cambiar_estado_mesa(
    db: AsyncSession, id_mesa: int, nuevo_estado: str
) -> Mesa:
    mesa = await get_mesa(db, id_mesa)
    _validate_mesa_transition(mesa.estado, nuevo_estado)
    mesa = await mesa_repo.update_mesa(db, mesa, {"estado": nuevo_estado})
    await db.commit()
    return mesa


# ── Reserva ───────────────────────────────────────────────────────────────────

async def get_reserva(db: AsyncSession, id_reserva: int) -> Reserva:
    reserva = await mesa_repo.get_reserva_by_id(db, id_reserva)
    if not reserva:
        raise MajesaError(f"Reserva {id_reserva} no encontrada", 404)
    return reserva


async def get_reservas(
    db: AsyncSession, id_mesa: int | None = None, estado: str | None = None
) -> list[Reserva]:
    return await mesa_repo.get_reservas(db, id_mesa=id_mesa, estado=estado)


async def create_reserva(
    db: AsyncSession, data: ReservaCreate, id_usuario: int
) -> Reserva:
    mesa = await get_mesa(db, data.id_mesa)
    if mesa.estado not in ("disponible", "reservada"):
        raise MajesaError(
            f"No se puede reservar una mesa en estado {mesa.estado!r}", 409
        )
    reserva = Reserva(
        **data.model_dump(),
        id_usuario=id_usuario,
        estado="pendiente",
        fecha_creacion=_now(),
    )
    reserva = await mesa_repo.create_reserva(db, reserva)
    # Mark mesa as reservada
    await mesa_repo.update_mesa(db, mesa, {"estado": "reservada"})
    await db.commit()
    return reserva


async def cambiar_estado_reserva(
    db: AsyncSession, id_reserva: int, nuevo_estado: str
) -> Reserva:
    reserva = await get_reserva(db, id_reserva)
    _validate_reserva_transition(reserva.estado, nuevo_estado)

    update_data: dict = {"estado": nuevo_estado}

    mesa = await mesa_repo.get_mesa_by_id(db, reserva.id_mesa)
    if mesa:
        if nuevo_estado == "completada":
            # Customer arrives — mesa becomes ocupada
            _validate_mesa_transition(mesa.estado, "ocupada")
            await mesa_repo.update_mesa(db, mesa, {"estado": "ocupada"})
        elif nuevo_estado == "cancelada" and mesa.estado == "reservada":
            await mesa_repo.update_mesa(db, mesa, {"estado": "disponible"})

    reserva = await mesa_repo.update_reserva(db, reserva, update_data)
    await db.commit()
    return reserva
async def delete_mesa(db: AsyncSession, id_mesa: int) -> None:
    """Soft delete: sets activo = False instead of deleting the record."""
    mesa = await get_mesa(db, id_mesa)
    await mesa_repo.update_mesa(db, mesa, {"activo": False})
    await db.commit()