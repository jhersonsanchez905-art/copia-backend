"""
Unit tests for VentaCreateRequest schema validators and VentaResponse computed fields.
No DB, no HTTP — pure Pydantic validation.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.venta_schema import (
    ItemVentaRequest,
    PagoRequest,
    VentaCreateRequest,
    VentaResponse,
)


# ── ItemVentaRequest ──────────────────────────────────────────────────────────

class TestItemVentaRequest:
    def test_cantidad_positiva_valida(self):
        item = ItemVentaRequest(id_producto=1, cantidad=3)
        assert item.cantidad == 3

    def test_cantidad_uno_valida(self):
        assert ItemVentaRequest(id_producto=1, cantidad=1).cantidad == 1

    def test_cantidad_default_es_uno(self):
        assert ItemVentaRequest(id_producto=1).cantidad == 1

    def test_cantidad_cero_invalida(self):
        with pytest.raises(ValidationError):
            ItemVentaRequest(id_producto=1, cantidad=0)

    def test_cantidad_negativa_invalida(self):
        with pytest.raises(ValidationError):
            ItemVentaRequest(id_producto=1, cantidad=-5)


# ── PagoRequest ───────────────────────────────────────────────────────────────

class TestPagoRequest:
    def test_monto_positivo_valido(self):
        pago = PagoRequest(id_metodo_pago=1, monto=Decimal("10000"))
        assert pago.monto == Decimal("10000")

    def test_monto_cero_invalido(self):
        with pytest.raises(ValidationError):
            PagoRequest(id_metodo_pago=1, monto=Decimal("0"))

    def test_monto_negativo_invalido(self):
        with pytest.raises(ValidationError):
            PagoRequest(id_metodo_pago=1, monto=Decimal("-500"))

    def test_url_comprobante_opcional(self):
        pago = PagoRequest(id_metodo_pago=1, monto=Decimal("5000"))
        assert pago.url_comprobante is None

    def test_url_comprobante_aceptada(self):
        pago = PagoRequest(
            id_metodo_pago=2, monto=Decimal("5000"), url_comprobante="https://example.com/recibo.jpg"
        )
        assert pago.url_comprobante == "https://example.com/recibo.jpg"


# ── VentaCreateRequest ────────────────────────────────────────────────────────

def _base_request(**overrides):
    defaults = {
        "turno": "manana",
        "id_apertura": 1,
        "productos": [{"id_producto": 1, "cantidad": 2}],
        "pagos": [{"id_metodo_pago": 1, "monto": "20000"}],
    }
    defaults.update(overrides)
    return VentaCreateRequest(**defaults)


class TestVentaCreateRequest:
    def test_request_valido(self):
        req = _base_request()
        assert len(req.productos) == 1
        assert len(req.pagos) == 1

    def test_productos_vacios_invalido(self):
        with pytest.raises(ValidationError) as exc:
            _base_request(productos=[])
        assert "al menos un producto" in str(exc.value)

    def test_pagos_vacios_invalido(self):
        with pytest.raises(ValidationError) as exc:
            _base_request(pagos=[])
        assert "al menos un pago" in str(exc.value)

    def test_productos_duplicados_invalido(self):
        with pytest.raises(ValidationError) as exc:
            _base_request(
                productos=[
                    {"id_producto": 1, "cantidad": 1},
                    {"id_producto": 1, "cantidad": 2},
                ]
            )
        assert "duplicados" in str(exc.value)

    def test_productos_distintos_valido(self):
        req = _base_request(
            productos=[
                {"id_producto": 1, "cantidad": 1},
                {"id_producto": 2, "cantidad": 1},
            ]
        )
        assert len(req.productos) == 2

    def test_dos_pagos_mismo_metodo_efectivo_valido(self):
        req = _base_request(
            pagos=[
                {"id_metodo_pago": 1, "monto": "8000"},
                {"id_metodo_pago": 1, "monto": "4000"},
            ]
        )
        assert len(req.pagos) == 2
        assert sum(p.monto for p in req.pagos) == Decimal("12000")

    def test_tres_pagos_misma_transferencia_valido(self):
        req = _base_request(
            pagos=[
                {"id_metodo_pago": 2, "monto": "5000", "url_comprobante": "https://x.com/a.jpg"},
                {"id_metodo_pago": 2, "monto": "5000", "url_comprobante": "https://x.com/b.jpg"},
                {"id_metodo_pago": 2, "monto": "5000", "url_comprobante": "https://x.com/c.jpg"},
            ]
        )
        assert len(req.pagos) == 3

    def test_pagos_metodos_mixtos_valido(self):
        req = _base_request(
            pagos=[
                {"id_metodo_pago": 1, "monto": "10000"},
                {"id_metodo_pago": 2, "monto": "5000", "url_comprobante": "https://x.com/r.jpg"},
                {"id_metodo_pago": 1, "monto": "3000"},
            ]
        )
        assert len(req.pagos) == 3
        assert sum(p.monto for p in req.pagos) == Decimal("18000")

    def test_cuatro_pagos_distintos_valido(self):
        req = _base_request(
            pagos=[
                {"id_metodo_pago": 1, "monto": "5000"},
                {"id_metodo_pago": 2, "monto": "5000", "url_comprobante": "https://x.com/1.jpg"},
                {"id_metodo_pago": 1, "monto": "5000"},
                {"id_metodo_pago": 3, "monto": "5000"},
            ]
        )
        assert len(req.pagos) == 4

    def test_multiples_metodos_pago_distintos_valido(self):
        req = _base_request(
            pagos=[
                {"id_metodo_pago": 1, "monto": "10000"},
                {"id_metodo_pago": 2, "monto": "10000"},
            ]
        )
        assert len(req.pagos) == 2

    def test_turno_invalido_rechazado(self):
        with pytest.raises(ValidationError):
            _base_request(turno="noche")

    def test_id_pedido_y_cliente_opcionales(self):
        req = _base_request()
        assert req.id_pedido is None
        assert req.id_cliente is None


# ── VentaResponse.cambio ──────────────────────────────────────────────────────

def _response(**overrides):
    defaults = {
        "id_venta": 1,
        "id_apertura": 1,
        "id_usuario": 1,
        "turno": "manana",
        "fecha": datetime.now(timezone.utc),
        "subtotal": Decimal("10000"),
        "total": Decimal("10000"),
        "estado": "completada",
    }
    defaults.update(overrides)
    return VentaResponse(**defaults)


class TestVentaResponseCambio:
    def test_pago_exacto_cambio_cero(self):
        r = _response(subtotal=Decimal("10000"), total=Decimal("10000"))
        assert r.cambio == Decimal("0")

    def test_pago_con_vuelto(self):
        r = _response(subtotal=Decimal("8000"), total=Decimal("10000"))
        assert r.cambio == Decimal("2000")

    def test_cambio_nunca_negativo(self):
        # total < subtotal should not happen in practice but must not return negative
        r = _response(subtotal=Decimal("10000"), total=Decimal("9000"))
        assert r.cambio == Decimal("0")

    def test_cambio_fraccionario(self):
        r = _response(subtotal=Decimal("9500"), total=Decimal("10000"))
        assert r.cambio == Decimal("500")
