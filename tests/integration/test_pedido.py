"""
Integration tests for the /pedidos endpoints.
Services are mocked to isolate HTTP layer behavior from business logic.
"""
from unittest.mock import AsyncMock, patch

from app.exceptions import MajesaError


# ── GET /pedidos ───────────────────────────────────────────────────────────────

def test_listar_pedidos_returns_empty_list(client_admin):
    with patch(
        "app.services.pedido_service.get_pedidos",
        new=AsyncMock(return_value=[]),
    ):
        resp = client_admin.get("/api/v1/pedidos")
    assert resp.status_code == 200
    assert resp.json() == []


def test_listar_pedidos_requires_auth(client_no_auth):
    resp = client_no_auth.get("/api/v1/pedidos")
    assert resp.status_code == 401


def test_listar_pedidos_accepts_estado_filter(client_admin):
    with patch(
        "app.services.pedido_service.get_pedidos",
        new=AsyncMock(return_value=[]),
    ) as mock:
        resp = client_admin.get("/api/v1/pedidos?estado=abierto")
        assert resp.status_code == 200
        mock.assert_called_once()
        _, kwargs = mock.call_args
        assert kwargs.get("estado") == "abierto"


def test_listar_pedidos_accepts_id_mesa_filter(client_admin):
    with patch(
        "app.services.pedido_service.get_pedidos",
        new=AsyncMock(return_value=[]),
    ) as mock:
        resp = client_admin.get("/api/v1/pedidos?id_mesa=3")
        assert resp.status_code == 200
        _, kwargs = mock.call_args
        assert kwargs.get("id_mesa") == 3


# ── POST /pedidos — validación de body ────────────────────────────────────────

def test_crear_pedido_missing_id_mesa_returns_422(client_mesero):
    resp = client_mesero.post("/api/v1/pedidos", json={
        "items": [],
        "servicios": [],
    })
    assert resp.status_code == 422


def test_crear_pedido_item_cantidad_cero_returns_422(client_mesero):
    resp = client_mesero.post("/api/v1/pedidos", json={
        "id_mesa": 1,
        "items": [{"id_producto": 1, "cantidad": 0, "precio_unitario": "10.00"}],
        "servicios": [],
    })
    assert resp.status_code == 422


def test_crear_pedido_item_cantidad_negativa_returns_422(client_mesero):
    resp = client_mesero.post("/api/v1/pedidos", json={
        "id_mesa": 1,
        "items": [{"id_producto": 1, "cantidad": -1}],
        "servicios": [],
    })
    assert resp.status_code == 422


def test_crear_pedido_body_vacio_returns_422(client_mesero):
    resp = client_mesero.post("/api/v1/pedidos", json={})
    assert resp.status_code == 422


# ── PATCH /pedidos/{id}/estado ────────────────────────────────────────────────

def test_cambiar_estado_pedido_not_found_returns_404(client_admin):
    with patch(
        "app.services.pedido_service.cambiar_estado_pedido",
        new=AsyncMock(side_effect=MajesaError("Pedido 999 no encontrado", 404)),
    ):
        resp = client_admin.patch("/api/v1/pedidos/999/estado?nuevo_estado=enviado")
    assert resp.status_code == 404
    assert "999" in resp.json()["error"]


def test_cambiar_estado_pedido_invalid_transition_returns_409(client_admin):
    with patch(
        "app.services.pedido_service.cambiar_estado_pedido",
        new=AsyncMock(side_effect=MajesaError("Transición inválida: pagado → abierto", 409)),
    ):
        resp = client_admin.patch("/api/v1/pedidos/1/estado?nuevo_estado=abierto")
    assert resp.status_code == 409


def test_cambiar_estado_pedido_missing_nuevo_estado_returns_422(client_admin):
    resp = client_admin.patch("/api/v1/pedidos/1/estado")
    assert resp.status_code == 422


# ── POST /pedidos/{id}/items ──────────────────────────────────────────────────

def test_agregar_item_missing_fields_returns_422(client_mesero):
    resp = client_mesero.post("/api/v1/pedidos/1/items", json={
        "id_producto": 1,
    })
    assert resp.status_code == 422


def test_agregar_item_pedido_cerrado_returns_409(client_mesero):
    with patch(
        "app.services.pedido_service.agregar_item",
        new=AsyncMock(side_effect=MajesaError("Solo se pueden agregar items a pedidos abiertos", 409)),
    ):
        resp = client_mesero.post("/api/v1/pedidos/1/items", json={
            "id_producto": 1,
            "cantidad": 2,
            "precio_unitario": "15.00",
        })
    assert resp.status_code == 409


# ── PATCH /pedidos/items/{id}/estado ──────────────────────────────────────────

def test_cambiar_estado_item_not_found_returns_404(client_mesero):
    with patch(
        "app.services.pedido_service.cambiar_estado_item",
        new=AsyncMock(side_effect=MajesaError("PedidoItem 5 no encontrado", 404)),
    ):
        resp = client_mesero.patch("/api/v1/pedidos/items/5/estado?nuevo_estado=listo")
    assert resp.status_code == 404


def test_cambiar_estado_item_transicion_invalida_returns_409(client_admin):
    with patch(
        "app.services.pedido_service.cambiar_estado_item",
        new=AsyncMock(side_effect=MajesaError("Transición de item inválida", 409)),
    ):
        resp = client_admin.patch("/api/v1/pedidos/items/1/estado?nuevo_estado=pendiente")
    assert resp.status_code == 409
