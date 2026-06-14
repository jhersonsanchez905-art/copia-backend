"""
Unit tests for caja_service.cerrar_caja: el efectivo esperado y la
diferencia general deben considerar el monto_inicial (fondo de caja)
de la apertura, no solo las ventas del turno.
"""
import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.caja import AperturaCaja, Denominacion
from app.models.catalogo import MetodoPago
from app.schemas.caja_schema import (
    ArqueoDenominacionRequest,
    CierreCajaDetalleRequest,
    CierreCajaRequest,
)
from app.services import caja_service


@pytest.mark.asyncio
async def test_cierre_balanceado_considera_monto_inicial():
    apertura = AperturaCaja(
        id_apertura=1,
        id_usuario=1,
        turno="manana",
        fecha=datetime.date.today(),
        monto_inicial=Decimal("100000"),
    )
    metodo_efectivo = MetodoPago(
        id_metodo_pago=1, nombre="Efectivo", requiere_comprobante=False, activo=True
    )
    denominacion = Denominacion(
        id_denominacion=1, valor=Decimal("130000"), tipo="billete", activo=True
    )

    data = CierreCajaRequest(
        detalle=[CierreCajaDetalleRequest(id_metodo_pago=2, total_contado=Decimal("20000"))],
        arqueo_efectivo=[ArqueoDenominacionRequest(id_denominacion=1, cantidad=1)],
    )

    with patch.object(caja_service, "caja_repo") as repo:
        repo.get_apertura_sin_cierre = AsyncMock(return_value=apertura)
        repo.get_denominacion_by_id = AsyncMock(return_value=denominacion)
        repo.get_total_ventas_by_apertura = AsyncMock(return_value=Decimal("50000"))
        repo.get_totales_por_metodo_pago = AsyncMock(
            return_value={1: Decimal("30000"), 2: Decimal("20000")}
        )
        repo.get_metodo_pago_efectivo = AsyncMock(return_value=metodo_efectivo)
        repo.create_cierre = AsyncMock(side_effect=lambda cierre, db: cierre)
        repo.create_cierre_detalle = AsyncMock()
        repo.create_cierre_arqueo = AsyncMock()
        repo.get_cierre_by_apertura = AsyncMock()

        await caja_service.cerrar_caja(data, id_usuario=1, db=AsyncMock())

    cierre_creado = repo.create_cierre.call_args.args[0]
    # Caja balanceada: efectivo contado (130000) == fondo inicial (100000) + ventas en efectivo (30000)
    assert cierre_creado.diferencia == Decimal("0")

    detalle_efectivo = repo.create_cierre_detalle.call_args_list[0].args[0]
    assert detalle_efectivo.id_metodo_pago == 1
    assert detalle_efectivo.total_esperado == Decimal("130000")
    assert detalle_efectivo.diferencia == Decimal("0")
