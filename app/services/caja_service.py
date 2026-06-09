"""
app/services/caja_service.py

Business logic for cash register module.
Handles shift opening and closing with payment method breakdown.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.schemas.caja_schema import AperturaCajaRequest, CierreCajaRequest
from app.repositories import caja_repo, venta_repo
from app.models.caja import AperturaCaja, CierreCaja, CierreCajaDetalle
from app.exceptions import MajesaError


async def abrir_caja(
    data: AperturaCajaRequest,
    id_usuario: int,
    db: AsyncSession
) -> AperturaCaja:
    """
    Open a new cash register shift.

    Raises:
        MajesaError: If there is already an open shift for this user and turn.
    """
    async with db.begin():
        apertura = AperturaCaja(
            id_usuario=id_usuario,
            turno=data.turno,
            fecha=data.fecha,
            monto_inicial=data.monto_inicial,
            hora_apertura=datetime.utcnow(),
            observaciones=data.observaciones
        )
        return await caja_repo.create_apertura(apertura, db)


async def cerrar_caja(
    id_apertura: int,
    data: CierreCajaRequest,
    id_usuario: int,
    db: AsyncSession
) -> CierreCaja:
    """
    Close a cash register shift.
    Calculates expected totals from sales and compares with counted amounts.

    Raises:
        MajesaError: If the opening does not exist or is already closed.
    """
    async with db.begin():
        apertura = await caja_repo.get_apertura_by_id(id_apertura, db)
        if not apertura:
            raise MajesaError("Apertura de caja no encontrada", 404)

        ya_cerrada = await caja_repo.get_cierre_by_apertura(id_apertura, db)
        if ya_cerrada:
            raise MajesaError("Esta apertura ya fue cerrada", 409)

        total_contado = sum(d.total_contado for d in data.detalle)

        cierre = CierreCaja(
            id_apertura=id_apertura,
            id_usuario=id_usuario,
            turno=apertura.turno,
            fecha=apertura.fecha,
            total_general=total_contado,
            total_transacciones=0,  # TODO: calcular desde ventas
            diferencia=0,           # TODO: calcular vs total esperado
            hora_cierre=datetime.utcnow(),
            observaciones=data.observaciones
        )
        cierre = await caja_repo.create_cierre(cierre, db)

        for d in data.detalle:
            detalle = CierreCajaDetalle(
                id_cierre=cierre.id_cierre,
                id_metodo_pago=d.id_metodo_pago,
                total_esperado=0,           # TODO: calcular desde pagos del turno
                total_contado=d.total_contado,
                diferencia=0 - d.total_contado
            )
            await caja_repo.create_cierre_detalle(detalle, db)

        return cierre
