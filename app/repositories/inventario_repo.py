"""
app/repositories/inventario_repo.py

Data access layer for inventory module.
Only database queries here, no business logic.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from app.models.inventario import MovimientoInventario, Alerta
from app.models.insumo import Insumo


async def get_insumo_by_id(id_insumo: int, db: AsyncSession) -> Optional[Insumo]:
    """Retrieve a single supply item by its ID."""
    result = await db.execute(
        select(Insumo).where(Insumo.id_insumo == id_insumo)
    )
    return result.scalar_one_or_none()


async def update_stock(id_insumo: int, nuevo_stock: float, db: AsyncSession) -> None:
    """Update the stock of a supply item."""
    await db.execute(
        update(Insumo)
        .where(Insumo.id_insumo == id_insumo)
        .values(stock_actual=nuevo_stock)
    )


async def create_movimiento(movimiento: MovimientoInventario, db: AsyncSession) -> MovimientoInventario:
    """Persist an inventory movement to the database."""
    db.add(movimiento)
    await db.flush()
    await db.refresh(movimiento)
    return movimiento


async def get_movimiento_by_id(id_movimiento: int, db: AsyncSession) -> Optional[MovimientoInventario]:
    """Retrieve an inventory movement by its ID."""
    result = await db.execute(
        select(MovimientoInventario)
        .where(MovimientoInventario.id_movimiento == id_movimiento)
    )
    return result.scalar_one_or_none()


async def update_movimiento_estado(
    id_movimiento: int,
    estado: str,
    id_aprobador: int,
    db: AsyncSession
) -> None:
    """Update the status of an inventory movement."""
    await db.execute(
        update(MovimientoInventario)
        .where(MovimientoInventario.id_movimiento == id_movimiento)
        .values(estado=estado, id_aprobador=id_aprobador)
    )


async def get_alerta_activa_by_insumo(id_insumo: int, db: AsyncSession) -> Optional[Alerta]:
    """Retrieve an active alert for a given supply item if it exists."""
    result = await db.execute(
        select(Alerta)
        .where(
            Alerta.id_insumo == id_insumo,
            Alerta.estado == "activa"
        )
    )
    return result.scalar_one_or_none()


async def create_alerta(alerta: Alerta, db: AsyncSession) -> Alerta:
    """Persist a new inventory alert to the database."""
    db.add(alerta)
    await db.flush()
    return alerta


async def get_alertas_activas(db: AsyncSession) -> list[Alerta]:
    """Retrieve all active inventory alerts."""
    result = await db.execute(
        select(Alerta).where(Alerta.estado == "activa")
    )
    return result.scalars().all()


async def resolver_alerta(id_insumo: int, db: AsyncSession) -> None:
    """Mark an active alert as resolved for a given supply item."""
    from datetime import datetime
    await db.execute(
        update(Alerta)
        .where(
            Alerta.id_insumo == id_insumo,
            Alerta.estado == "activa"
        )
        .values(estado="resuelta", fecha_resolucion=datetime.utcnow())
    )
