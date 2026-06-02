"""
producto_repo.py
Capa de acceso a datos para Producto.
Author: SebastianValero12
Issue: #40
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto


async def get_all(
    db: AsyncSession,
    *,
    solo_activos: bool = True,
    id_categoria: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Producto]:
    query = select(Producto)
    if solo_activos:
        query = query.where(Producto.activo.is_(True))
    if id_categoria is not None:
        query = query.where(Producto.id_categoria == id_categoria)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count(
    db: AsyncSession,
    *,
    solo_activos: bool = True,
    id_categoria: int | None = None,
) -> int:
    query = select(func.count(Producto.id_producto))
    if solo_activos:
        query = query.where(Producto.activo.is_(True))
    if id_categoria is not None:
        query = query.where(Producto.id_categoria == id_categoria)
    result = await db.execute(query)
    return result.scalar_one()


async def get_by_id(db: AsyncSession, producto_id: int) -> Producto | None:
    return await db.get(Producto, producto_id)


async def create(db: AsyncSession, producto: Producto) -> Producto:
    db.add(producto)
    await db.flush()
    await db.refresh(producto)
    return producto


async def update(
    db: AsyncSession, producto: Producto, data: dict
) -> Producto:
    for key, value in data.items():
        setattr(producto, key, value)
    await db.flush()
    await db.refresh(producto)
    return producto


async def delete(db: AsyncSession, producto: Producto) -> None:
    await db.delete(producto)
    await db.flush()