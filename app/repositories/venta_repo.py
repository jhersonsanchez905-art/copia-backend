"""
app/repositories/venta_repo.py

Data access layer for sales module.
Only database queries here, no business logic.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date
from typing import Optional
from app.models.venta import Venta, ItemVenta, Pago, Factura


async def create_venta(venta: Venta, db: AsyncSession) -> Venta:
    """Persist a new sale to the database."""
    db.add(venta)
    await db.flush()
    await db.refresh(venta)
    return venta


async def get_venta_by_id(id_venta: int, db: AsyncSession) -> Optional[Venta]:
    """Retrieve a single sale by its ID including items, payments and invoice."""
    result = await db.execute(
        select(Venta)
        .options(
            selectinload(Venta.items),
            selectinload(Venta.pagos),
            selectinload(Venta.factura)
        )
        .where(Venta.id_venta == id_venta)
    )
    return result.scalar_one_or_none()


async def get_ventas_by_fecha_turno(
    fecha: date,
    turno: Optional[str],
    db: AsyncSession
) -> list[Venta]:
    """Retrieve all sales for a given date and optional shift."""
    query = select(Venta).where(Venta.fecha.cast(date) == fecha)
    if turno:
        query = query.where(Venta.turno == turno)
    result = await db.execute(query)
    return result.scalars().all()


async def create_item_venta(item: ItemVenta, db: AsyncSession) -> ItemVenta:
    """Persist a sale item to the database."""
    db.add(item)
    await db.flush()
    return item


async def create_pago(pago: Pago, db: AsyncSession) -> Pago:
    """Persist a payment record to the database."""
    db.add(pago)
    await db.flush()
    return pago


async def create_factura(factura: Factura, db: AsyncSession) -> Factura:
    """Persist an invoice to the database."""
    db.add(factura)
    await db.flush()
    return factura
