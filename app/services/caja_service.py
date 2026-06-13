"""
app/services/caja_service.py

Business logic for cash register module.
Handles shift opening and closing with payment method breakdown and denomination tracking.

Author: Suley Suarez
Issue: #16
"""
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.caja import (
    AperturaCaja,
    AperturaCajaArqueo,
    CierreCaja,
    CierreCajaArqueo,
    CierreCajaDetalle,
)
from app.repositories import caja_repo
from app.schemas.caja_schema import AperturaCajaRequest, CierreCajaRequest


async def _validar_arqueo(
    lineas: list,
    db: AsyncSession,
) -> list[tuple]:
    """
    Validate denomination lines against the DB catalogue.
    Returns a list of (id_denominacion, cantidad, subtotal, valor) tuples.
    Raises MajesaError on any unknown or inactive denomination.
    """
    resultado = []
    for linea in lineas:
        den = await caja_repo.get_denominacion_by_id(linea.id_denominacion, db)
        if not den:
            raise MajesaError(
                f"Denominación {linea.id_denominacion} no encontrada", 404
            )
        if not den.activo:
            raise MajesaError(
                f"Denominación {den.valor} no está activa", 422
            )
        subtotal = Decimal(str(den.valor)) * linea.cantidad
        resultado.append((den.id_denominacion, linea.cantidad, subtotal))
    return resultado


async def get_denominaciones(db: AsyncSession):
    """Return the catalogue of active denominations."""
    return await caja_repo.get_denominaciones_activas(db)


async def abrir_caja(
    data: AperturaCajaRequest,
    id_usuario: int,
    db: AsyncSession,
) -> AperturaCaja:
    """
    Open a new cash register shift.

    Raises:
        MajesaError 409: If there is already an open (unclosed) shift for this user.
        MajesaError 404/422: If any denomination in the arqueo is invalid.
    """
    # Block if this user already has an open shift (any turno/fecha)
    existente = await caja_repo.get_apertura_sin_cierre(id_usuario, db)
    if existente:
        raise MajesaError(
            f"Ya existe una apertura activa (id={existente.id_apertura}) para este usuario. "
            "Cierra el turno actual antes de abrir uno nuevo.",
            409,
        )

    # Block if any user has an OPEN (unclosed) apertura for this same turno+fecha
    abierta = await caja_repo.get_apertura_abierta_por_turno_fecha(data.turno, data.fecha, db)
    if abierta:
        raise MajesaError(
            "Ya existe una apertura abierta para este turno y fecha",
            409,
        )

    # RN-03: block new opening if any previous-day apertura is unclosed (any user)
    anterior = await caja_repo.get_apertura_sin_cierre_anterior(db)
    if anterior:
        raise MajesaError(
            f"Existe una apertura de turno anterior sin cerrar (id={anterior.id_apertura}). "
            "Cierra ese turno antes de abrir uno nuevo.",
            409,
        )

    # Validate denominations before writing anything
    lineas_arqueo = await _validar_arqueo(data.arqueo, db)

    monto_inicial = sum(subtotal for _, _, subtotal in lineas_arqueo)

    apertura = AperturaCaja(
        id_usuario=id_usuario,
        turno=data.turno,
        fecha=data.fecha,
        monto_inicial=monto_inicial,
        hora_apertura=datetime.now(timezone.utc),
        observaciones=data.observaciones,
    )

    try:
        apertura = await caja_repo.create_apertura(apertura, db)
        for id_den, cantidad, subtotal in lineas_arqueo:
            await caja_repo.create_apertura_arqueo(
                AperturaCajaArqueo(
                    id_apertura=apertura.id_apertura,
                    id_denominacion=id_den,
                    cantidad=cantidad,
                    subtotal=subtotal,
                ),
                db,
            )
    except IntegrityError:
        await db.rollback()
        raise MajesaError("Conflicto al crear apertura de caja", 409)

    # Reload with arqueo + denominacion eagerly loaded for proper serialization
    return await caja_repo.get_apertura_by_id(apertura.id_apertura, db)


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
    Calculates expected totals from completed sales and compares with counted amounts.

    Raises:
        MajesaError 404: If there is no active opening for this user.
        MajesaError 404/422: If any denomination in the arqueo_efectivo is invalid.
    """
    apertura = await caja_repo.get_apertura_sin_cierre(id_usuario, db)
    if not apertura:
        raise MajesaError("No hay apertura de caja activa para este usuario", 404)

    # Validate denominations before any writes
    lineas_arqueo = await _validar_arqueo(data.arqueo_efectivo, db)

    # Compute cash total from denomination counts — cashier never enters it manually
    total_efectivo_arqueo = sum(subtotal for _, _, subtotal in lineas_arqueo)

    total_transacciones = await caja_repo.get_total_ventas_by_apertura(
        apertura.id_apertura, db
    )
    totales_por_metodo = await caja_repo.get_totales_por_metodo_pago(
        apertura.id_apertura, db
    )

    # Identify the cash payment method (requiere_comprobante = False)
    metodo_efectivo = await caja_repo.get_metodo_pago_efectivo(db)
    if not metodo_efectivo:
        raise MajesaError(
            "No se encontró un método de pago de efectivo configurado en el sistema", 422
        )

    # Guard: detalle must NOT include the cash method (it's auto-computed from arqueo)
    ids_detalle = {d.id_metodo_pago for d in data.detalle}
    if metodo_efectivo.id_metodo_pago in ids_detalle:
        raise MajesaError(
            f"El método de pago '{metodo_efectivo.nombre}' no debe incluirse en detalle — "
            "su total se calcula automáticamente del arqueo de denominaciones.",
            422,
        )

    total_contado = total_efectivo_arqueo + sum(
        (d.total_contado for d in data.detalle), Decimal(0)
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
        hora_cierre=datetime.now(timezone.utc),
        observaciones=data.observaciones,
    )
    cierre = await caja_repo.create_cierre(cierre, db)

    # Auto-create the cash detalle row from arqueo sum
    total_esperado_efectivo = totales_por_metodo.get(
        metodo_efectivo.id_metodo_pago, Decimal(0)
    )
    await caja_repo.create_cierre_detalle(
        CierreCajaDetalle(
            id_cierre=cierre.id_cierre,
            id_metodo_pago=metodo_efectivo.id_metodo_pago,
            total_esperado=total_esperado_efectivo,
            total_contado=total_efectivo_arqueo,
            diferencia=total_efectivo_arqueo - total_esperado_efectivo,
        ),
        db,
    )

    # Create detalle rows for non-cash payment methods
    for d in data.detalle:
        total_esperado = totales_por_metodo.get(d.id_metodo_pago, Decimal(0))
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

    for id_den, cantidad, subtotal in lineas_arqueo:
        await caja_repo.create_cierre_arqueo(
            CierreCajaArqueo(
                id_cierre=cierre.id_cierre,
                id_denominacion=id_den,
                cantidad=cantidad,
                subtotal=subtotal,
            ),
            db,
        )

    # Reload with all relationships eagerly loaded for proper serialization
    return await caja_repo.get_cierre_by_apertura(apertura.id_apertura, db)


async def get_cierres(db: AsyncSession) -> list[CierreCaja]:
    """Return all cash register closings ordered by most recent first."""
    return await caja_repo.get_cierres(db)


async def get_cierre(id_cierre: int, db: AsyncSession) -> CierreCaja:
    """Return a specific closing with its full breakdown."""
    cierre = await caja_repo.get_cierre_by_id(id_cierre, db)
    if not cierre:
        raise MajesaError(f"Cierre {id_cierre} no encontrado", 404)
    return cierre
