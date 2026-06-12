"""
mesa_service.py
Async business logic for Mesa with state machine enforcement.
Mesa states: disponible → ocupada | reservada → disponible

Reserva logic has been moved to reserva_service.py (single source of truth).

Author: Suley Suarez / SebastianValero12
Issue: fix/reservas-transferencias
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.mesa import Mesa
from app.repositories import mesa_repo
from app.schemas.mesa_schema import (
    MesaCreate,
    MesaUpdate,
)


_MESA_TRANSITIONS: dict[str, set[str]] = {
    "disponible": {"ocupada", "reservada"},
    "ocupada": {"disponible"},
    "reservada": {"ocupada", "disponible"},
}


def _validate_mesa_transition(current: str, next_state: str) -> None:
    allowed = _MESA_TRANSITIONS.get(current, set())
    if next_state not in allowed:
        raise MajesaError(
            f"Transición de mesa inválida: {current!r} → {next_state!r}. "
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
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay campos para actualizar",
        )
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