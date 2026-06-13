"""
Unit tests for registrar_venta pre-flight validations.
No real DB — all repos are patched with AsyncMock.
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import MajesaError
from app.schemas.venta_schema import ItemVentaRequest, PagoRequest, VentaCreateRequest
from app.services import venta_service


# ── helpers ───────────────────────────────────────────────────────────────────

def _req(**overrides):
    defaults = dict(
        turno="manana",
        id_apertura=1,
        id_pedido=None,
        id_cliente=None,
        productos=[ItemVentaRequest(id_producto=1, cantidad=1)],
        pagos=[PagoRequest(id_metodo_pago=1, monto=Decimal("10000"))],
    )
    defaults.update(overrides)
    return VentaCreateRequest(**defaults)


def _apertura(id_usuario=1):
    a = MagicMock()
    a.id_apertura = 1
    a.id_usuario = id_usuario
    return a


def _producto(activo=True, nombre="Café", precio=Decimal("5000")):
    p = MagicMock()
    p.activo = activo
    p.nombre = nombre
    p.precio = precio
    return p


def _metodo(activo=True, nombre="Efectivo", requiere_comprobante=False):
    m = MagicMock()
    m.activo = activo
    m.nombre = nombre
    m.requiere_comprobante = requiere_comprobante
    return m


# ── tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAperturaValidations:
    async def test_apertura_no_encontrada_retorna_404(self):
        db = AsyncMock()
        with patch("app.services.venta_service.caja_repo") as mock_caja:
            mock_caja.get_apertura_by_id = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 404
        assert "Apertura" in exc.value.message

    async def test_apertura_cerrada_retorna_409(self):
        db = AsyncMock()
        with patch("app.services.venta_service.caja_repo") as mock_caja:
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=MagicMock())
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 409

    async def test_cajero_apertura_ajena_retorna_403(self):
        db = AsyncMock()
        with patch("app.services.venta_service.caja_repo") as mock_caja:
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura(id_usuario=99))
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db, es_admin=False)
        assert exc.value.code == 403

    async def test_admin_puede_usar_apertura_ajena(self):
        """Admin must NOT raise 403 for a foreign apertura — test reaches product check."""
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura(id_usuario=99))
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=None)  # will raise 404, not 403
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db, es_admin=True)
        assert exc.value.code != 403


@pytest.mark.asyncio
class TestPedidoValidations:
    async def test_pedido_no_encontrado_retorna_404(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.pedido_repo") as mock_ped,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_ped.get_pedido_with_mesa = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_pedido=7), 1, db)
        assert exc.value.code == 404

    async def test_pedido_no_enviado_retorna_422(self):
        db = AsyncMock()
        pedido = MagicMock(estado="abierto", mesa=None)
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.pedido_repo") as mock_ped,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_ped.get_pedido_with_mesa = AsyncMock(return_value=pedido)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_pedido=7), 1, db)
        assert exc.value.code == 422

    async def test_pedido_ya_pagado_retorna_409(self):
        db = AsyncMock()
        pedido = MagicMock(estado="enviado", mesa=MagicMock(estado="ocupada"))
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.pedido_repo") as mock_ped,
            patch("app.services.venta_service.venta_repo") as mock_venta,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_ped.get_pedido_with_mesa = AsyncMock(return_value=pedido)
            mock_venta.get_venta_completada_by_pedido = AsyncMock(return_value=MagicMock())
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_pedido=7), 1, db)
        assert exc.value.code == 409
        assert "ya tiene una venta completada" in exc.value.message

    async def test_mesa_disponible_bloquea_cobro(self):
        db = AsyncMock()
        pedido = MagicMock(estado="enviado", mesa=MagicMock(estado="disponible", numero="5"))
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.pedido_repo") as mock_ped,
            patch("app.services.venta_service.venta_repo") as mock_venta,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_ped.get_pedido_with_mesa = AsyncMock(return_value=pedido)
            mock_venta.get_venta_completada_by_pedido = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_pedido=7), 1, db)
        assert exc.value.code == 409
        assert "no está en estado válido" in exc.value.message


def _cliente(activo=True):
    c = MagicMock()
    c.activo = activo
    return c


@pytest.mark.asyncio
class TestClienteValidation:
    async def test_cliente_no_encontrado_retorna_404(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_cat.get_cliente_by_id = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_cliente=99), 1, db)
        assert exc.value.code == 404
        assert "Cliente" in exc.value.message

    async def test_cliente_inactivo_retorna_422(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_cat.get_cliente_by_id = AsyncMock(return_value=_cliente(activo=False))
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(id_cliente=99), 1, db)
        assert exc.value.code == 422
        assert "activo" in exc.value.message.lower()


@pytest.mark.asyncio
class TestProductoValidations:
    async def test_producto_no_encontrado_retorna_404(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 404
        assert "Producto" in exc.value.message

    async def test_producto_inactivo_retorna_422(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto(activo=False))
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 422
        assert "no está disponible" in exc.value.message


@pytest.mark.asyncio
class TestMetodoPagoValidations:
    async def _setup_until_pagos(self, mock_caja, mock_prod):
        mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
        mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
        mock_prod.get_by_id = AsyncMock(return_value=_producto())

    async def test_metodo_no_encontrado_retorna_404(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
        ):
            await self._setup_until_pagos(mock_caja, mock_prod)
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 404
        assert "Método de pago" in exc.value.message

    async def test_metodo_inactivo_retorna_422(self):
        db = AsyncMock()
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
        ):
            await self._setup_until_pagos(mock_caja, mock_prod)
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo(activo=False))
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
        assert exc.value.code == 422
        assert "no está activo" in exc.value.message

    async def test_transferencia_sin_comprobante_retorna_422(self):
        db = AsyncMock()
        pagos = [PagoRequest(id_metodo_pago=2, monto=Decimal("10000"), url_comprobante=None)]
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
        ):
            await self._setup_until_pagos(mock_caja, mock_prod)
            mock_cat.get_metodo_pago_by_id = AsyncMock(
                return_value=_metodo(activo=True, nombre="Transferencia", requiere_comprobante=True)
            )
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(pagos=pagos), 1, db)
        assert exc.value.code == 422
        assert "comprobante" in exc.value.message.lower()

    async def test_transferencia_con_comprobante_pasa_validacion(self):
        """A transfer with a URL must NOT raise a comprobante error — reaches recipe check."""
        db = AsyncMock()
        pagos = [
            PagoRequest(id_metodo_pago=2, monto=Decimal("10000"), url_comprobante="https://x.com/p.jpg")
        ]
        with (
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
        ):
            await self._setup_until_pagos(mock_caja, mock_prod)
            mock_cat.get_metodo_pago_by_id = AsyncMock(
                return_value=_metodo(activo=True, nombre="Transferencia", requiere_comprobante=True)
            )
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(pagos=pagos), 1, db)
        # Must fail at recipe check, not at comprobante check
        assert exc.value.code == 422
        assert "receta" in exc.value.message.lower()
