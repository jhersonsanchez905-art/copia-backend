"""
app/repositories/caja_repo.py

Data access layer for cash register module.
Only database queries here, no business logic.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from app.models.caja import AperturaCaja, CierreCaja, CierreCajaDetalle


async def create_apertura(apertura: AperturaCaja, db: AsyncSession) -> AperturaCaja:
    """Persist a cash register opening to the database."""
    db.add(apertura)
    await db.flush()
    await db.refresh(apertura)
    return apertura


async def get_apertura_by_id(id_apertura: int, db: AsyncSession) -> Optional[AperturaCaja]:
    """Retrieve a cash register opening by its ID."""
    result = await db.execute(
        select(AperturaCaja).where(AperturaCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()


async def get_apertura_activa(id_usuario: int, turno: str, db: AsyncSession) -> Optional[AperturaCaja]:
    """Retrieve the active opening for a user and shift if it exists."""
    result = await db.execute(
        select(AperturaCaja)
        .where(
            AperturaCaja.id_usuario == id_usuario,
            AperturaCaja.turno == turno
        )
        .order_by(AperturaCaja.hora_apertura.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_cierre(cierre: CierreCaja, db: AsyncSession) -> CierreCaja:
    """Persist a cash register closing to the database."""
    db.add(cierre)
    await db.flush()
    await db.refresh(cierre)
    return cierre


async def create_cierre_detalle(detalle: CierreCajaDetalle, db: AsyncSession) -> CierreCajaDetalle:
    """Persist a payment method detail for a cash register closing."""
    db.add(detalle)
    await db.flush()
    return detalle


async def get_cierre_by_apertura(id_apertura: int, db: AsyncSession) -> Optional[CierreCaja]:
    """Retrieve the closing associated to a given opening."""
    result = await db.execute(
        select(CierreCaja)
        .options(selectinload(CierreCaja.detalle))
        .where(CierreCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()
