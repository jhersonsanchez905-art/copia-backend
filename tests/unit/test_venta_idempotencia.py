"""
Unit tests for the idempotency layer in VentaCreateRequest (schema)
and registrar_venta (service).

Schema tests: token normalisation and length constraints.
Service tests: sequential retry, concurrent IntegrityError, null token.
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from app.exceptions import MajesaError
from app.schemas.venta_schema import ItemVentaRequest, PagoRequest, VentaCreateRequest
from app.services import venta_service


# ── schema helpers ─────────────────────────────────────────────────────────────

def _base(**overrides):
    defaults = {
        "turno": "manana",
        "id_apertura": 1,
        "productos": [{"id_producto": 1, "cantidad": 1}],
        "pagos": [{"id_metodo_pago": 1, "monto": "10000"}],
    }
    defaults.update(overrides)
    return VentaCreateRequest(**defaults)


# ── Schema: token normalisation ────────────────────────────────────────────────

class TestTokenNormalizacion:
    def test_none_queda_none(self):
        assert _base(token_idempotencia=None).token_idempotencia is None

    def test_token_valido_conservado(self):
        req = _base(token_idempotencia="sale-abc-2026")
        assert req.token_idempotencia == "sale-abc-2026"

    def test_espacios_recortados(self):
        req = _base(token_idempotencia="  sale-abc  ")
        assert req.token_idempotencia == "sale-abc"

    def test_cadena_vacia_se_convierte_en_none(self):
        assert _base(token_idempotencia="").token_idempotencia is None

    def test_solo_espacios_se_convierte_en_none(self):
        assert _base(token_idempotencia="   ").token_idempotencia is None

    def test_token_exactamente_64_caracteres_valido(self):
        token = "a" * 64
        assert _base(token_idempotencia=token).token_idempotencia == token

    def test_token_65_caracteres_invalido(self):
        with pytest.raises(ValidationError):
            _base(token_idempotencia="a" * 65)

    def test_uuid_tipico_valido(self):
        token = "sale-8c7e3f4a-2b3d-4e5f-9012-abcdef012345"
        assert _base(token_idempotencia=token).token_idempotencia == token


# ── service helpers ────────────────────────────────────────────────────────────

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


def _apertura():
    a = MagicMock()
    a.id_apertura = 1
    a.id_usuario = 1
    return a


def _producto():
    p = MagicMock()
    p.activo = True
    p.nombre = "Café"
    p.precio = Decimal("5000")
    return p


def _metodo():
    m = MagicMock()
    m.activo = True
    m.nombre = "Efectivo"
    m.requiere_comprobante = False
    return m


def _version_sin_insumos():
    v = MagicMock()
    v.id_receta_version = 1
    v.id_producto = 1
    v.version = 1
    v.detalles_insumo = []
    v.detalles_subreceta = []
    return v


def _venta_existente(id_venta=42):
    v = MagicMock()
    v.id_venta = id_venta
    v.token_idempotencia = "tok-abc"
    return v


def _integrity_error_token():
    """Simulate a PostgreSQL UniqueViolationError on token_idempotencia."""
    class _Orig:
        def __str__(self):
            return 'duplicate key value violates unique constraint "uq_venta_token_idempotencia"'
    return SAIntegrityError("INSERT INTO pos.venta ...", {}, _Orig())


# ── Service: sequential retry (token already committed) ───────────────────────

@pytest.mark.asyncio
class TestIdempotenciaSecuencial:
    async def test_retry_devuelve_venta_existente_sin_consultas_adicionales(self):
        """If the token is already committed, return immediately without running
        any business logic — no apertura, product, or stock queries."""
        db = AsyncMock()
        existing = _venta_existente()
        with patch("app.services.venta_service.venta_repo") as mock_venta:
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=existing)
            result = await venta_service.registrar_venta(
                _req(token_idempotencia="tok-abc"), 1, db
            )
        assert result is existing
        mock_venta.get_by_idempotency_token.assert_awaited_once_with(db, "tok-abc")

    async def test_retry_no_crea_nueva_venta(self):
        db = AsyncMock()
        existing = _venta_existente()
        with patch("app.services.venta_service.venta_repo") as mock_venta:
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=existing)
            await venta_service.registrar_venta(_req(token_idempotencia="tok-abc"), 1, db)
            mock_venta.create_venta.assert_not_called()

    async def test_retry_no_descuenta_inventario(self):
        db = AsyncMock()
        existing = _venta_existente()
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.inventario_service") as mock_inv,
        ):
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=existing)
            await venta_service.registrar_venta(_req(token_idempotencia="tok-abc"), 1, db)
            mock_inv.descontar_stock.assert_not_called()

    async def test_retry_no_crea_pagos(self):
        db = AsyncMock()
        existing = _venta_existente()
        with patch("app.services.venta_service.venta_repo") as mock_venta:
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=existing)
            await venta_service.registrar_venta(_req(token_idempotencia="tok-abc"), 1, db)
            mock_venta.create_pago.assert_not_called()

    async def test_retry_no_crea_factura(self):
        db = AsyncMock()
        existing = _venta_existente()
        with patch("app.services.venta_service.venta_repo") as mock_venta:
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=existing)
            await venta_service.registrar_venta(_req(token_idempotencia="tok-abc"), 1, db)
            mock_venta.create_factura.assert_not_called()

    async def test_primer_request_crea_venta_normalmente(self):
        """No existing token → the pre-check passes through to the full flow."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        nueva_venta = MagicMock(id_venta=1)
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
            patch("app.services.venta_service.stock_repo") as mock_stock,
            patch("app.services.venta_service.inventario_service"),
        ):
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=None)
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto())
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo())
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=_version_sin_insumos())
            mock_stock.get_stocks_by_insumos_for_update = AsyncMock(return_value={})
            mock_venta.create_venta = AsyncMock(return_value=nueva_venta)
            mock_venta.create_item_venta = AsyncMock()
            mock_venta.create_pago = AsyncMock()
            mock_venta.create_factura = AsyncMock()
            mock_venta.get_venta_by_id = AsyncMock(return_value=nueva_venta)
            result = await venta_service.registrar_venta(
                _req(token_idempotencia="tok-nuevo"), 1, db
            )
        assert result is nueva_venta
        mock_venta.create_venta.assert_awaited_once()

    async def test_token_diferente_crea_nueva_venta(self):
        """Two requests with different tokens → each creates its own sale."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        nueva_venta = MagicMock(id_venta=2)
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
            patch("app.services.venta_service.stock_repo") as mock_stock,
            patch("app.services.venta_service.inventario_service"),
        ):
            # "tok-nuevo" has no existing sale
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=None)
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto())
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo())
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=_version_sin_insumos())
            mock_stock.get_stocks_by_insumos_for_update = AsyncMock(return_value={})
            mock_venta.create_venta = AsyncMock(return_value=nueva_venta)
            mock_venta.create_item_venta = AsyncMock()
            mock_venta.create_pago = AsyncMock()
            mock_venta.create_factura = AsyncMock()
            mock_venta.get_venta_by_id = AsyncMock(return_value=nueva_venta)
            result = await venta_service.registrar_venta(
                _req(token_idempotencia="tok-nuevo"), 1, db
            )
        assert result.id_venta == 2


# ── Service: null token behaves normally ──────────────────────────────────────

@pytest.mark.asyncio
class TestSinToken:
    async def test_sin_token_no_consulta_idempotencia(self):
        """None token skips the idempotency pre-check entirely."""
        db = AsyncMock()
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
        ):
            mock_caja.get_apertura_by_id = AsyncMock(return_value=None)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(), 1, db)
            mock_venta.get_by_idempotency_token.assert_not_called()
        assert exc.value.code == 404


# ── Service: concurrent duplicate (IntegrityError path) ───────────────────────

@pytest.mark.asyncio
class TestIdempotenciaConcurrente:
    async def test_integrity_error_token_devuelve_venta_ganadora(self):
        """Concurrent duplicate: pre-check misses, INSERT fails, fetch winner."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        existing = _venta_existente(id_venta=99)
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
            patch("app.services.venta_service.stock_repo") as mock_stock,
            patch("app.services.venta_service.inventario_service"),
        ):
            # Pre-check: token not yet visible (other request hasn't committed)
            # Second call (after rollback): winner's sale is now visible
            mock_venta.get_by_idempotency_token = AsyncMock(side_effect=[None, existing])
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto())
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo())
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=_version_sin_insumos())
            mock_stock.get_stocks_by_insumos_for_update = AsyncMock(return_value={})
            mock_venta.create_venta = AsyncMock(side_effect=_integrity_error_token())
            result = await venta_service.registrar_venta(
                _req(token_idempotencia="tok-race"), 1, db
            )
        assert result is existing
        assert result.id_venta == 99

    async def test_integrity_error_sin_token_propaga_409(self):
        """IntegrityError from a non-token constraint is re-raised as 409."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

        class _OtroConstraint:
            def __str__(self):
                return 'duplicate key value violates unique constraint "uq_venta_id_pedido"'

        other_error = SAIntegrityError("INSERT", {}, _OtroConstraint())
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
            patch("app.services.venta_service.stock_repo") as mock_stock,
            patch("app.services.venta_service.inventario_service"),
        ):
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=None)
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto())
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo())
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=_version_sin_insumos())
            mock_stock.get_stocks_by_insumos_for_update = AsyncMock(return_value={})
            mock_venta.create_venta = AsyncMock(side_effect=other_error)
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(token_idempotencia="tok-x"), 1, db)
        assert exc.value.code == 409

    async def test_integrity_error_token_sin_ganador_propaga_409(self):
        """Race: both requests rolled back — winner not found → 409, let client retry."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        with (
            patch("app.services.venta_service.venta_repo") as mock_venta,
            patch("app.services.venta_service.caja_repo") as mock_caja,
            patch("app.services.venta_service.producto_repo") as mock_prod,
            patch("app.services.venta_service.catalogo_repo") as mock_cat,
            patch("app.services.venta_service.receta_repo") as mock_rec,
            patch("app.services.venta_service.stock_repo") as mock_stock,
            patch("app.services.venta_service.inventario_service"),
        ):
            # Both pre-check and post-rollback lookup return None
            mock_venta.get_by_idempotency_token = AsyncMock(return_value=None)
            mock_caja.get_apertura_by_id = AsyncMock(return_value=_apertura())
            mock_caja.get_cierre_by_apertura = AsyncMock(return_value=None)
            mock_prod.get_by_id = AsyncMock(return_value=_producto())
            mock_cat.get_metodo_pago_by_id = AsyncMock(return_value=_metodo())
            mock_rec.get_vigente_by_producto = AsyncMock(return_value=_version_sin_insumos())
            mock_stock.get_stocks_by_insumos_for_update = AsyncMock(return_value={})
            mock_venta.create_venta = AsyncMock(side_effect=_integrity_error_token())
            with pytest.raises(MajesaError) as exc:
                await venta_service.registrar_venta(_req(token_idempotencia="tok-y"), 1, db)
        assert exc.value.code == 409
