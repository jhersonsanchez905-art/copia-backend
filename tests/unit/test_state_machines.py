"""
Unit tests for pedido and item state-machine logic.
No DB, no HTTP — pure function calls.
"""
import pytest

from app.exceptions import MajesaError
from app.services.pedido_service import (
    _ITEM_TRANSITIONS,
    _PEDIDO_TRANSITIONS,
    _validate_pedido_transition,
)


class TestPedidoTransitions:
    def test_abierto_to_enviado_is_valid(self):
        _validate_pedido_transition("abierto", "enviado")

    def test_abierto_to_cancelado_is_valid(self):
        _validate_pedido_transition("abierto", "cancelado")

    def test_enviado_to_pagado_is_valid(self):
        _validate_pedido_transition("enviado", "pagado")

    def test_enviado_to_cancelado_is_valid(self):
        _validate_pedido_transition("enviado", "cancelado")

    def test_abierto_cannot_jump_to_pagado(self):
        with pytest.raises(MajesaError) as exc:
            _validate_pedido_transition("abierto", "pagado")
        assert exc.value.code == 409

    def test_pagado_is_terminal(self):
        for target in ("abierto", "enviado", "cancelado"):
            with pytest.raises(MajesaError) as exc:
                _validate_pedido_transition("pagado", target)
            assert exc.value.code == 409

    def test_cancelado_is_terminal(self):
        with pytest.raises(MajesaError) as exc:
            _validate_pedido_transition("cancelado", "abierto")
        assert exc.value.code == 409

    def test_unknown_current_state_raises(self):
        with pytest.raises(MajesaError):
            _validate_pedido_transition("desconocido", "enviado")

    def test_all_valid_states_covered(self):
        expected = {"abierto", "enviado", "pagado", "cancelado"}
        assert set(_PEDIDO_TRANSITIONS.keys()) == expected

    def test_error_message_contains_states(self):
        with pytest.raises(MajesaError) as exc:
            _validate_pedido_transition("pagado", "abierto")
        assert "pagado" in exc.value.message
        assert "abierto" in exc.value.message


class TestItemTransitions:
    def test_pendiente_to_en_preparacion(self):
        assert "en_preparacion" in _ITEM_TRANSITIONS["pendiente"]

    def test_pendiente_to_cancelado(self):
        assert "cancelado" in _ITEM_TRANSITIONS["pendiente"]

    def test_en_preparacion_to_listo(self):
        assert "listo" in _ITEM_TRANSITIONS["en_preparacion"]

    def test_en_preparacion_to_cancelado(self):
        assert "cancelado" in _ITEM_TRANSITIONS["en_preparacion"]

    def test_listo_to_entregado(self):
        assert "entregado" in _ITEM_TRANSITIONS["listo"]

    def test_listo_cannot_go_to_pendiente(self):
        assert "pendiente" not in _ITEM_TRANSITIONS["listo"]

    def test_entregado_is_terminal(self):
        assert _ITEM_TRANSITIONS["entregado"] == set()

    def test_cancelado_is_terminal(self):
        assert _ITEM_TRANSITIONS["cancelado"] == set()

    def test_all_item_states_covered(self):
        expected = {"pendiente", "en_preparacion", "listo", "entregado", "cancelado"}
        assert set(_ITEM_TRANSITIONS.keys()) == expected
