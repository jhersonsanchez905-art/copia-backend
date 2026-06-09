"""
devolucion_repo.py
Async repository for Devolucion (returns).

<<<<<<< HEAD
Author: Jherson
=======
Author: SebasValero12
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
Issue: #40
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.venta import Devolucion, ItemVenta, Venta


async def get_devolucion_by_id(
    db: AsyncSession, id_devolucion: int
) -> Optional[Devolucion]:
    result = await db.execute(
        select(Devolucion)
        .options(
            selectinload(Devolucion.item_venta),
            selectinload(Devolucion.venta),
        )
        .where(Devolucion.id_devolucion == id_devolucion)
    )
    return result.scalar_one_or_none()


async def get_devoluciones(
    db: AsyncSession, estado: str | None = None
) -> list[Devolucion]:
    query = select(Devolucion)
    if estado:
        query = query.where(Devolucion.estado == estado)
    query = query.order_by(Devolucion.fecha.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_devolucion(
    db: AsyncSession, devolucion: Devolucion
) -> Devolucion:
    db.add(devolucion)
    await db.flush()
    await db.refresh(devolucion)
    return devolucion


async def update_devolucion(
    db: AsyncSession, devolucion: Devolucion, data: dict
) -> Devolucion:
    for key, value in data.items():
        setattr(devolucion, key, value)
    await db.flush()
    await db.refresh(devolucion)
    return devolucion


async def get_venta_by_id(db: AsyncSession, id_venta: int) -> Optional[Venta]:
    result = await db.execute(
        select(Venta).where(Venta.id_venta == id_venta)
    )
    return result.scalar_one_or_none()


async def get_item_venta_by_id(
    db: AsyncSession, id_item_venta: int
) -> Optional[ItemVenta]:
    return await db.get(ItemVenta, id_item_venta)
