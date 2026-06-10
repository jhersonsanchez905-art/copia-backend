"""
caja_service.py
Async business logic for cash register module.
Handles shift opening and closing with payment method breakdown.

Author: Suley Suarez / Jherson
Issue: #16, #40
"""
import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.caja import AperturaCaja, CierreCaja, CierreCajaDetalle
from app.repositories import caja_repo
from app.schemas.caja_schema import AperturaCajaRequest, CierreCajaRequest


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── Apertura ──────────────────────────────────────────────────────────────────

async def abrir_caja(
    data: AperturaCajaRequest,
    id_usuario: int,
    db: AsyncSession,
) -> AperturaCaja:
    """
    Open a new cash register shift.
    Validates that no other apertura exists for the same turno and fecha.
    """
    existente = await caja_repo.get_apertura_by_turno_fecha(
        data.turno, data.fecha, db
    )
    if existente:
        raise MajesaError(
            f"Ya existe una apertura para el turno '{data.turno}' "
            f"en la fecha {data.fecha}",
            409,
        )

    apertura = AperturaCaja(
        id_usuario=id_usuario,
        turno=data.turno,
        fecha=data.fecha,
        monto_inicial=data.monto_inicial,
        hora_apertura=_now(),
        observaciones=data.observaciones,
    )
    apertura = await caja_repo.create_apertura(apertura, db)
    await db.commit()
    return apertura


async def get_apertura_activa(db: AsyncSession) -> AperturaCaja:
    """Return the currently open (not yet closed) apertura."""
    apertura = await caja_repo.get_apertura_activa_sin_cierre(db)
    if not apertura:
        raise MajesaError("No hay apertura de caja activa", 404)
    return apertura


# ── Cierre ────────────────────────────────────────────────────────────────────

async def cerrar_caja(
    data: CierreCajaRequest,
    id_usuario: int,
    db: AsyncSession,
) -> CierreCaja:
    """
    Close the currently active cash register shift.
    Calculates expected totals from sales and compares with counted amounts.
    """
    apertura = await caja_repo.get_apertura_activa_sin_cierre(db)
    if not apertura:
        raise MajesaError("No hay apertura de caja activa para cerrar", 404)

    ya_cerrada = await caja_repo.get_cierre_by_apertura(
        apertura.id_apertura, db
    )
    if ya_cerrada:
        raise MajesaError("Esta apertura ya fue cerrada", 409)

    total_transacciones = await caja_repo.get_total_ventas_by_apertura(
        apertura.id_apertura, db
    )
    totales_por_metodo = await caja_repo.get_totales_por_metodo_pago(
        apertura.id_apertura, db
    )

    total_contado = sum(
        float(d.total_contado) for d in data.detalle
    )
    diferencia_general = total_contado - total_transacciones

    cierre = CierreCaja(
        id_apertura=apertura.id_apertura,
        id_usuario=id_usuario,
        turno=apertura.turno,
        fecha=apertura.fecha,
        total_general=total_contado,
        total_transacciones=total_transacciones,
        diferencia=diferencia_general,
        hora_cierre=_now(),
        observaciones=data.observaciones,
    )
    cierre = await caja_repo.create_cierre(cierre, db)

    for d in data.detalle:
        total_esperado = Decimal(
            str(totales_por_metodo.get(d.id_metodo_pago, 0))
        )
        detalle = CierreCajaDetalle(
            id_cierre=cierre.id_cierre,
            id_metodo_pago=d.id_metodo_pago,
            total_esperado=total_esperado,
            total_contado=d.total_contado,
            diferencia=d.total_contado - total_esperado,
        )
        await caja_repo.create_cierre_detalle(detalle, db)

    await db.commit()
    return await caja_repo.get_cierre_by_id(cierre.id_cierre, db)


async def get_cierres(db: AsyncSession) -> list[CierreCaja]:
    return await caja_repo.get_cierres(db)


async def get_cierre(db: AsyncSession, id_cierre: int) -> CierreCaja:
    cierre = await caja_repo.get_cierre_by_id(id_cierre, db)
    if not cierre:
        raise MajesaError(f"Cierre {id_cierre} no encontrado", 404)
    return cierre
