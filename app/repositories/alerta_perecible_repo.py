"""
alerta_perecible_repo.py
Async repository for AlertaPerecible.
Includes evaluation logic based on last inventory entry movement.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alerta_perecible import AlertaPerecible
from app.models.inventario import MovimientoInventario
from app.models.stock import Stock


async def get_alerta_perecible_by_id(
    db: AsyncSession, id_alerta: int
) -> AlertaPerecible | None:
    return await db.get(AlertaPerecible, id_alerta)


async def get_alertas_perecibles(
    db: AsyncSession,
    estado: str | None = None,
    id_insumo: int | None = None,
) -> list[AlertaPerecible]:
    query = select(AlertaPerecible)
    if estado:
        query = query.where(AlertaPerecible.estado == estado)
    if id_insumo:
        query = query.where(AlertaPerecible.id_insumo == id_insumo)
    query = query.order_by(AlertaPerecible.fecha_creacion.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_ultimo_movimiento_entrada(
    db: AsyncSession, id_insumo: int
) -> MovimientoInventario | None:
    """Get the last entrada movement for a given insumo."""
    result = await db.execute(
        select(MovimientoInventario)
        .where(
            MovimientoInventario.id_insumo == id_insumo,
            MovimientoInventario.tipo == "entrada",
        )
        .order_by(MovimientoInventario.fecha.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_stocks_activos(db: AsyncSession) -> list[Stock]:
    """Get all stocks with quantity greater than 0."""
    result = await db.execute(
        select(Stock).where(Stock.cantidad > 0)
    )
    return list(result.scalars().all())


async def get_alerta_perecible_activa(
    db: AsyncSession, id_insumo: int, id_stock: int
) -> AlertaPerecible | None:
    """Check if there is already an active alert for this insumo/stock."""
    result = await db.execute(
        select(AlertaPerecible).where(
            AlertaPerecible.id_insumo == id_insumo,
            AlertaPerecible.id_stock == id_stock,
            AlertaPerecible.estado == "activa",
        )
    )
    return result.scalar_one_or_none()


async def create_alerta_perecible(
    db: AsyncSession, alerta: AlertaPerecible
) -> AlertaPerecible:
    """Create a new perishable alert."""
    db.add(alerta)
    await db.flush()
    await db.refresh(alerta)
    return alerta