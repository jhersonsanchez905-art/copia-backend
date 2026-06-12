"""
pago_repo.py
Async repository for Pago model.
Provides data access for payment validation (RF-012).

Author: SebastianValero12
Issue: RF-012 — fix/reservas-transferencias
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.venta import Pago


async def get_by_id(db: AsyncSession, id_pago: int) -> Pago | None:
    """Fetch a Pago by PK, eagerly loading metodo_pago for validation checks."""
    result = await db.execute(
        select(Pago)
        .options(selectinload(Pago.metodo_pago))
        .where(Pago.id_pago == id_pago)
    )
    return result.scalar_one_or_none()


async def update(db: AsyncSession, pago: Pago, data: dict) -> Pago:
    """Apply a dict of changes to a Pago instance and flush."""
    for key, value in data.items():
        setattr(pago, key, value)
    await db.flush()
    await db.refresh(pago)
    return pago