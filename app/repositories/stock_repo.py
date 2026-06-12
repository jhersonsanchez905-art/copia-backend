"""
stock_repo.py
Async repository for Stock.
Stock is updated automatically by the system — never directly via API.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.stock import Stock


async def get_stocks_by_insumos(db: AsyncSession, ids: list[int]) -> dict[int, "Stock"]:
    result = await db.execute(select(Stock).where(Stock.id_insumo.in_(ids)))
    return {s.id_insumo: s for s in result.scalars().all()}


async def get_stock_by_insumo(db: AsyncSession, id_insumo: int) -> Stock | None:
    result = await db.execute(
        select(Stock)
        .options(selectinload(Stock.insumo))
        .where(Stock.id_insumo == id_insumo)
    )
    return result.scalar_one_or_none()


async def get_stock_by_id(db: AsyncSession, id_stock: int) -> Stock | None:
    return await db.get(Stock, id_stock)


async def get_all_stocks(
    db: AsyncSession,
    semaforo: str | None = None,
) -> list[Stock]:
    query = select(Stock)
    if semaforo:
        query = query.where(Stock.semaforo == semaforo)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_stock(db: AsyncSession, stock: Stock) -> Stock:
    db.add(stock)
    await db.flush()
    await db.refresh(stock)
    return stock


async def update_stock(
    db: AsyncSession,
    stock: Stock,
    nueva_cantidad,
    nuevo_semaforo: str,
) -> Stock:
    stock.cantidad = nueva_cantidad
    stock.semaforo = nuevo_semaforo
    await db.flush()
    await db.refresh(stock)
    return stock
