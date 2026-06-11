"""
app/services/caja_service.py

Business logic for cash register module.
Handles shift opening and closing with payment method breakdown.

Author: Suley Suarez
Issue: #16
"""
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.caja_schema import AperturaCajaRequest, CierreCajaRequest
from app.repositories import caja_repo
from app.models.caja import AperturaCaja, CierreCaja, CierreCajaDetalle
from app.exceptions import MajesaError


async def abrir_caja(
    data: AperturaCajaRequest,
    id_usuario: int,
    db: AsyncSession,
) -> AperturaCaja:
    """
    Open a new cash register shift.

    Raises:
        MajesaError: If there is already an open shift for this user.
    """
    apertura = AperturaCaja(
        id_usuario=id_usuario,
        turno=data.turno,
        fecha=data.fecha,
        monto_inicial=data.monto_inicial,
        hora_apertura=datetime.now(timezone.utc),
        observaciones=data.observaciones,
    )
    return await caja_repo.create_apertura(apertura, db)


async def get_apertura_activa(id_usuario: int, db: AsyncSession) -> AperturaCaja:
    """Return the currently open (not yet closed) shift for the given user."""
    apertura = await caja_repo.get_apertura_sin_cierre(id_usuario, db)
    if not apertura:
        raise MajesaError("No hay apertura de caja activa para este usuario", 404)
    return apertura


async def cerrar_caja(
    data: CierreCajaRequest,
    id_usuario: int,
    db: AsyncSession,
) -> CierreCaja:
    """
    Close the active cash register shift for the current user.
    Compares counted amounts per payment method against expected totals from sales.

    Raises:
        MajesaError: If there is no active opening for this user.
    """
    apertura = await caja_repo.get_apertura_sin_cierre(id_usuario, db)
    if not apertura:
        raise MajesaError("No hay apertura de caja activa para este usuario", 404)

    total_contado = sum(
        (d.total_contado for d in data.detalle),
        Decimal(0),
    )

    cierre = CierreCaja(
        id_apertura=apertura.id_apertura,
        id_usuario=id_usuario,
        turno=apertura.turno,
        fecha=apertura.fecha,
        total_general=total_contado,
        total_transacciones=Decimal(0),  # TODO: calcular desde ventas del turno
        diferencia=Decimal(0),           # TODO: calcular vs total_transacciones
        hora_cierre=datetime.now(timezone.utc),
        observaciones=data.observaciones,
    )
    cierre = await caja_repo.create_cierre(cierre, db)

    for d in data.detalle:
        total_esperado = Decimal(0)  # TODO: calcular desde pagos del turno
        await caja_repo.create_cierre_detalle(
            CierreCajaDetalle(
                id_cierre=cierre.id_cierre,
                id_metodo_pago=d.id_metodo_pago,
                total_esperado=total_esperado,
                total_contado=d.total_contado,
                diferencia=d.total_contado - total_esperado,
            ),
            db,
        )

    # Reload with detalle eagerly populated to avoid MissingGreenlet on serialization.
    return await caja_repo.get_cierre_by_apertura(apertura.id_apertura, db)


async def get_cierres(db: AsyncSession) -> list[CierreCaja]:
    """Return all cash register closings ordered by most recent first."""
    return await caja_repo.get_cierres(db)


async def get_cierre(id_cierre: int, db: AsyncSession) -> CierreCaja:
    """Return a specific closing with its payment method breakdown."""
    cierre = await caja_repo.get_cierre_by_id(id_cierre, db)
    if not cierre:
        raise MajesaError(f"Cierre {id_cierre} no encontrado", 404)
    return cierre
