"""
reserva_repo.py
Async repository for Reserva model. Mesa state side-effects are handled by the service.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mesa import Reserva


async def get_by_id(db: AsyncSession, id_reserva: int) -> Reserva | None:
    return await db.get(Reserva, id_reserva)


async def get_many(
    db: AsyncSession,
    id_mesa: int | None = None,
    estado: str | None = None,
<<<<<<< HEAD
=======
    fecha: str | None = None,
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
    skip: int = 0,
    limit: int = 50,
) -> list[Reserva]:
    q = select(Reserva)
    if id_mesa is not None:
        q = q.where(Reserva.id_mesa == id_mesa)
    if estado is not None:
        q = q.where(Reserva.estado == estado)
<<<<<<< HEAD
=======
    if fecha is not None:
        q = q.where(Reserva.fecha_hora >= fecha, Reserva.fecha_hora < fecha + " 23:59:59")
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
    q = q.order_by(Reserva.fecha_hora.asc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create(db: AsyncSession, reserva: Reserva) -> Reserva:
    db.add(reserva)
    await db.flush()
    await db.refresh(reserva)
    return reserva


async def update(db: AsyncSession, reserva: Reserva, data: dict) -> Reserva:
    for key, value in data.items():
        setattr(reserva, key, value)
    await db.flush()
    await db.refresh(reserva)
    return reserva
