"""
stock_service.py
Read-only async service for Stock semaforo status.
Stock values are modified only by inventario_service (via venta or approved adjustment).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.stock import Stock
from app.repositories import stock_repo


async def get_stock_by_insumo(db: AsyncSession, id_insumo: int) -> Stock:
    stock = await stock_repo.get_stock_by_insumo(db, id_insumo)
    if not stock:
        raise MajesaError(f"No existe registro de stock para insumo {id_insumo}", 404)
    return stock


async def get_all_stocks(
    db: AsyncSession, semaforo: str | None = None
) -> list[Stock]:
    return await stock_repo.get_all_stocks(db, semaforo=semaforo)
