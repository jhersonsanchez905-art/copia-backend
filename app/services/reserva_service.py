"""
reserva_service.py
Async business logic for Reserva with state machine enforcement.
State machine:
  pendiente  → confirmada (admin) | cancelada (admin)
  confirmada → completada         | cancelada (admin)
  completada → (terminal)
  cancelada  → (terminal)

Mesa side-effects:
  crear_reserva:    mesa disponible → reservada
  cancelar_reserva: mesa reservada → disponible
  completar_reserva: mesa reservada → ocupada (customer has arrived)
"""
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError, PermisoDenegadoError
from app.models.mesa import Mesa, Reserva
from app.repositories import mesa_repo, reserva_repo
from app.schemas.reserva_schema import ReservaCreate, ReservaUpdate


_TRANSITIONS: dict[str, set[str]] = {
    "pendiente": {"confirmada", "cancelada"},
    "confirmada": {"completada", "cancelada"},
    "completada": set(),
    "cancelada": set(),
}

_ADMIN_ONLY_STATES: set[str] = {"confirmada", "cancelada"}


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _assert_transition(current: str, target: str) -> None:
    allowed = _TRANSITIONS.get(current, set())
    if target not in allowed:
        raise MajesaError(
            f"Transición de reserva inválida: {current!r} → {target!r}. "
            f"Permitidas: {sorted(allowed) or 'ninguna'}",
            409,
        )


# ── Queries ───────────────────────────────────────────────────────────────────

async def get_reserva(db: AsyncSession, id_reserva: int) -> Reserva:
    reserva = await reserva_repo.get_by_id(db, id_reserva)
    if not reserva:
        raise MajesaError(f"Reserva {id_reserva} no encontrada", 404)
    return reserva


async def get_reservas(
    db: AsyncSession,
    id_mesa: int | None = None,
    estado: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Reserva]:
    return await reserva_repo.get_many(
<<<<<<< HEAD
        db, id_mesa=id_mesa, estado=estado, skip=skip, limit=limit
=======
      db, id_mesa=id_mesa, estado=estado, fecha=fecha, skip=skip, limit=limit
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
    )


# ── Mutations ─────────────────────────────────────────────────────────────────

async def crear_reserva(
    db: AsyncSession, data: ReservaCreate, id_usuario: int
) -> Reserva:
    mesa = await mesa_repo.get_mesa_by_id(db, data.id_mesa)
    if not mesa or not mesa.activo:
        raise MajesaError(f"Mesa {data.id_mesa} no encontrada o inactiva", 404)
    if mesa.estado not in ("disponible", "reservada"):
        raise MajesaError(
            f"No se puede reservar la mesa en estado {mesa.estado!r}", 409
        )

    reserva = Reserva(
        **data.model_dump(),
        id_usuario=id_usuario,
        estado="pendiente",
        fecha_creacion=_now(),
    )
    reserva = await reserva_repo.create(db, reserva)

    if mesa.estado == "disponible":
        await mesa_repo.update_mesa(db, mesa, {"estado": "reservada"})

    await db.commit()
    return reserva


async def actualizar_reserva(
    db: AsyncSession, id_reserva: int, data: ReservaUpdate
) -> Reserva:
    reserva = await get_reserva(db, id_reserva)
    if reserva.estado != "pendiente":
        raise MajesaError(
            "Solo se pueden editar reservas en estado pendiente", 409
        )
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise MajesaError("No hay campos para actualizar", 422)
    reserva = await reserva_repo.update(db, reserva, fields)
    await db.commit()
    return reserva


async def confirmar_reserva(
    db: AsyncSession, id_reserva: int, id_usuario: int, es_administrador: bool
) -> Reserva:
    if not es_administrador:
        raise PermisoDenegadoError()
    reserva = await get_reserva(db, id_reserva)
    _assert_transition(reserva.estado, "confirmada")
    reserva = await reserva_repo.update(db, reserva, {"estado": "confirmada"})
    await db.commit()
    return reserva


async def cancelar_reserva(
    db: AsyncSession, id_reserva: int, id_usuario: int, es_administrador: bool
) -> Reserva:
    if not es_administrador:
        raise PermisoDenegadoError()
    reserva = await get_reserva(db, id_reserva)
    _assert_transition(reserva.estado, "cancelada")

    mesa = await mesa_repo.get_mesa_by_id(db, reserva.id_mesa)
    if mesa and mesa.estado == "reservada":
        await mesa_repo.update_mesa(db, mesa, {"estado": "disponible"})

    reserva = await reserva_repo.update(db, reserva, {"estado": "cancelada"})
    await db.commit()
    return reserva


async def completar_reserva(db: AsyncSession, id_reserva: int) -> Reserva:
    """Customer has arrived — mesa transitions from reservada → ocupada."""
    reserva = await get_reserva(db, id_reserva)
    _assert_transition(reserva.estado, "completada")

    mesa = await mesa_repo.get_mesa_by_id(db, reserva.id_mesa)
    if mesa and mesa.estado == "reservada":
        await mesa_repo.update_mesa(db, mesa, {"estado": "ocupada"})

    reserva = await reserva_repo.update(db, reserva, {"estado": "completada"})
    await db.commit()
    return reserva
