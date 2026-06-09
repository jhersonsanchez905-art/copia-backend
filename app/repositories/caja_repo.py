"""
caja_repo.py
Async repository for AperturaCaja, CierreCaja, and CierreCajaDetalle.

Author: Suley Suarez / Jherson
Issue: #16, #40
"""
from datetime import date as date_type
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.caja import AperturaCaja, CierreCaja, CierreCajaDetalle
from app.models.venta import Pago, Venta


# ── AperturaCaja ──────────────────────────────────────────────────────────────

async def create_apertura(apertura: AperturaCaja, db: AsyncSession) -> AperturaCaja:
    db.add(apertura)
    await db.flush()
    await db.refresh(apertura)
    return apertura


async def get_apertura_by_id(id_apertura: int, db: AsyncSession) -> Optional[AperturaCaja]:
    result = await db.execute(
        select(AperturaCaja).where(AperturaCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()


async def get_apertura_by_turno_fecha(
    turno: str, fecha: date_type, db: AsyncSession
) -> Optional[AperturaCaja]:
    """Check if an opening already exists for the given shift and date."""
    result = await db.execute(
        select(AperturaCaja).where(
            AperturaCaja.turno == turno,
            AperturaCaja.fecha == fecha,
        )
    )
    return result.scalar_one_or_none()


async def get_apertura_activa(
    id_usuario: int, turno: str, db: AsyncSession
) -> Optional[AperturaCaja]:
    """Retrieve the active opening for a user and shift if it exists."""
    result = await db.execute(
        select(AperturaCaja)
        .where(
            AperturaCaja.id_usuario == id_usuario,
            AperturaCaja.turno == turno,
        )
        .order_by(AperturaCaja.hora_apertura.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_apertura_activa_sin_cierre(db: AsyncSession) -> Optional[AperturaCaja]:
    """Return the latest opening that has NOT been closed yet."""
    subq = select(CierreCaja.id_apertura)
    result = await db.execute(
        select(AperturaCaja)
        .where(AperturaCaja.id_apertura.notin_(subq))
        .order_by(AperturaCaja.hora_apertura.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ── CierreCaja ────────────────────────────────────────────────────────────────

async def create_cierre(cierre: CierreCaja, db: AsyncSession) -> CierreCaja:
    db.add(cierre)
    await db.flush()
    await db.refresh(cierre)
    return cierre


async def create_cierre_detalle(
    detalle: CierreCajaDetalle, db: AsyncSession
) -> CierreCajaDetalle:
    db.add(detalle)
    await db.flush()
    return detalle


async def get_cierre_by_apertura(
    id_apertura: int, db: AsyncSession
) -> Optional[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(selectinload(CierreCaja.detalles))
        .where(CierreCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()


async def get_cierres(db: AsyncSession) -> list[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(selectinload(CierreCaja.detalles))
        .order_by(CierreCaja.hora_cierre.desc())
    )
    return list(result.scalars().all())


async def get_cierre_by_id(
    id_cierre: int, db: AsyncSession
) -> Optional[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(selectinload(CierreCaja.detalles))
        .where(CierreCaja.id_cierre == id_cierre)
    )
    return result.scalar_one_or_none()


# ── Queries de ventas para cierre ─────────────────────────────────────────────

async def get_total_ventas_by_apertura(
    id_apertura: int, db: AsyncSession
) -> float:
    """Sum of all completed sale totals for a given apertura."""
    result = await db.execute(
        select(func.coalesce(func.sum(Venta.total), 0)).where(
            Venta.id_apertura == id_apertura,
            Venta.estado == "completada",
        )
    )
    return float(result.scalar_one())


async def get_totales_por_metodo_pago(
    id_apertura: int, db: AsyncSession
) -> dict[int, float]:
    """Sum of payment amounts grouped by id_metodo_pago for a given apertura."""
    result = await db.execute(
        select(
            Pago.id_metodo_pago,
            func.coalesce(func.sum(Pago.monto), 0),
        )
        .join(Venta, Venta.id_venta == Pago.id_venta)
        .where(
            Venta.id_apertura == id_apertura,
            Venta.estado == "completada",
        )
        .group_by(Pago.id_metodo_pago)
    )
    return {row[0]: float(row[1]) for row in result.all()}
