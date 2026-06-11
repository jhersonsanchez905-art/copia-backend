"""
app/repositories/caja_repo.py

Data access layer for cash register module.
Only database queries here, no business logic.

Author: Suley Suarez
Issue: #16
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.caja import (
    AperturaCaja,
    AperturaCajaArqueo,
    CierreCaja,
    CierreCajaArqueo,
    CierreCajaDetalle,
    Denominacion,
)
from app.models.venta import Pago, Venta


# ── helpers to eager-load all nested relationships ─────────────────────────────

def _apertura_options():
    return [
        selectinload(AperturaCaja.arqueo).selectinload(AperturaCajaArqueo.denominacion),
    ]


def _cierre_options():
    return [
        selectinload(CierreCaja.detalle),
        selectinload(CierreCaja.arqueo_efectivo).selectinload(CierreCajaArqueo.denominacion),
    ]


# ── Denominacion ──────────────────────────────────────────────────────────────

async def get_denominaciones_activas(db: AsyncSession) -> list[Denominacion]:
    """Return all active denominations ordered by value descending."""
    result = await db.execute(
        select(Denominacion)
        .where(Denominacion.activo.is_(True))
        .order_by(Denominacion.valor.desc())
    )
    return list(result.scalars().all())


async def get_denominacion_by_id(
    id_denominacion: int, db: AsyncSession
) -> Optional[Denominacion]:
    result = await db.execute(
        select(Denominacion).where(Denominacion.id_denominacion == id_denominacion)
    )
    return result.scalar_one_or_none()


# ── AperturaCaja ──────────────────────────────────────────────────────────────

async def create_apertura(apertura: AperturaCaja, db: AsyncSession) -> AperturaCaja:
    db.add(apertura)
    await db.flush()
    await db.refresh(apertura)
    return apertura


async def get_apertura_by_id(id_apertura: int, db: AsyncSession) -> Optional[AperturaCaja]:
    result = await db.execute(
        select(AperturaCaja)
        .options(*_apertura_options())
        .where(AperturaCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()


async def get_apertura_activa(
    id_usuario: int, turno: str, db: AsyncSession
) -> Optional[AperturaCaja]:
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


async def get_apertura_sin_cierre(
    id_usuario: int, db: AsyncSession
) -> Optional[AperturaCaja]:
    """Return the most recent unclosed opening for a user, with arqueo eagerly loaded."""
    result = await db.execute(
        select(AperturaCaja)
        .options(*_apertura_options())
        .outerjoin(CierreCaja, CierreCaja.id_apertura == AperturaCaja.id_apertura)
        .where(
            AperturaCaja.id_usuario == id_usuario,
            CierreCaja.id_cierre.is_(None),
        )
        .order_by(AperturaCaja.hora_apertura.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_apertura_arqueo(
    arqueo: AperturaCajaArqueo, db: AsyncSession
) -> AperturaCajaArqueo:
    db.add(arqueo)
    await db.flush()
    return arqueo


# ── Sales aggregates ──────────────────────────────────────────────────────────

async def get_total_ventas_by_apertura(id_apertura: int, db: AsyncSession) -> Decimal:
    """Sum of all completed sale totals for a given apertura."""
    result = await db.execute(
        select(func.coalesce(func.sum(Venta.total), 0)).where(
            Venta.id_apertura == id_apertura,
            Venta.estado == "completada",
        )
    )
    return Decimal(str(result.scalar_one()))


async def get_totales_por_metodo_pago(
    id_apertura: int, db: AsyncSession
) -> dict[int, Decimal]:
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
    return {row[0]: Decimal(str(row[1])) for row in result.all()}


# ── CierreCaja ────────────────────────────────────────────────────────────────

async def create_cierre(cierre: CierreCaja, db: AsyncSession) -> CierreCaja:
    """Persist closing and return it with its generated id_cierre."""
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


async def create_cierre_arqueo(
    arqueo: CierreCajaArqueo, db: AsyncSession
) -> CierreCajaArqueo:
    db.add(arqueo)
    await db.flush()
    return arqueo


async def get_cierre_by_apertura(
    id_apertura: int, db: AsyncSession
) -> Optional[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(*_cierre_options())
        .where(CierreCaja.id_apertura == id_apertura)
    )
    return result.scalar_one_or_none()


async def get_cierres(db: AsyncSession) -> list[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(*_cierre_options())
        .order_by(CierreCaja.hora_cierre.desc())
    )
    return list(result.scalars().all())


async def get_cierre_by_id(id_cierre: int, db: AsyncSession) -> Optional[CierreCaja]:
    result = await db.execute(
        select(CierreCaja)
        .options(*_cierre_options())
        .where(CierreCaja.id_cierre == id_cierre)
    )
    return result.scalar_one_or_none()
