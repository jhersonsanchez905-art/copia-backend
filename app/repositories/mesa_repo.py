"""
mesa_repo.py
Async repository for Mesa and Reserva.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mesa import Mesa, Reserva


# ── Mesa ──────────────────────────────────────────────────────────────────────

async def get_mesa_by_id(db: AsyncSession, id_mesa: int) -> Mesa | None:
    return await db.get(Mesa, id_mesa)


async def get_mesa_by_numero(db: AsyncSession, numero: str) -> Mesa | None:
    result = await db.execute(
        select(Mesa).where(Mesa.numero == numero)
    )
    return result.scalar_one_or_none()


async def get_mesas(
    db: AsyncSession,
    estado: str | None = None,
    solo_activas: bool = True,
) -> list[Mesa]:
    query = select(Mesa)
    if solo_activas:
        query = query.where(Mesa.activo.is_(True))
    if estado:
        query = query.where(Mesa.estado == estado)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_mesa(db: AsyncSession, mesa: Mesa) -> Mesa:
    db.add(mesa)
    await db.flush()
    await db.refresh(mesa)
    return mesa


async def update_mesa(db: AsyncSession, mesa: Mesa, data: dict) -> Mesa:
    for key, value in data.items():
        setattr(mesa, key, value)
    await db.flush()
    await db.refresh(mesa)
    return mesa


# ── Reserva ───────────────────────────────────────────────────────────────────

async def get_reserva_by_id(db: AsyncSession, id_reserva: int) -> Reserva | None:
    return await db.get(Reserva, id_reserva)


async def get_reservas(
    db: AsyncSession,
    id_mesa: int | None = None,
    estado: str | None = None,
) -> list[Reserva]:
    query = select(Reserva)
    if id_mesa:
        query = query.where(Reserva.id_mesa == id_mesa)
    if estado:
        query = query.where(Reserva.estado == estado)
    query = query.order_by(Reserva.fecha_hora.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_reserva(db: AsyncSession, reserva: Reserva) -> Reserva:
    db.add(reserva)
    await db.flush()
    await db.refresh(reserva)
    return reserva


async def update_reserva(db: AsyncSession, reserva: Reserva, data: dict) -> Reserva:
    for key, value in data.items():
        setattr(reserva, key, value)
    await db.flush()
    await db.refresh(reserva)
    return reserva
