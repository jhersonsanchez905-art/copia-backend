"""
Integration tests for authentication and role enforcement.
Each test verifies that a specific role is blocked or allowed by a specific endpoint.
Role-forbidden tests need no service mock — the dependency fails first.
Role-allowed tests mock the service to avoid hitting the real DB chain.
"""
from unittest.mock import AsyncMock, patch

from app.exceptions import MajesaError


# ── GET /auth/me ───────────────────────────────────────────────────────────────

def test_me_returns_200_for_authenticated_user(client_admin, admin_user):
    resp = client_admin.get("/api/v1/auth/me")
    assert resp.status_code == 200


def test_me_returns_user_fields(client_admin, admin_user):
    data = client_admin.get("/api/v1/auth/me").json()
    assert data["nombre"] == admin_user.nombre
    assert data["correo"] == admin_user.correo
    assert data["activo"] is True


def test_me_returns_401_without_auth(client_no_auth):
    resp = client_no_auth.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ── POST /pedidos — mesero y administrador únicamente ─────────────────────────

def test_cajero_can_crear_pedido(client_cajero):
    resp = client_cajero.post("/api/v1/pedidos", json={
        "id_mesa": 1,
        "items": [],
        "servicios": [],
    })
    assert resp.status_code != 403


def test_mesero_can_reach_crear_pedido_endpoint(client_mesero):
    # Role allowed — service fails (mock db), but must NOT return 403
    resp = client_mesero.post("/api/v1/pedidos", json={
        "id_mesa": 1,
        "items": [],
        "servicios": [],
    })
    assert resp.status_code != 403


def test_admin_can_reach_crear_pedido_endpoint(client_admin):
    resp = client_admin.post("/api/v1/pedidos", json={
        "id_mesa": 1,
        "items": [],
        "servicios": [],
    })
    assert resp.status_code != 403


# ── POST /caja/apertura — cajero y administrador únicamente ───────────────────

def test_mesero_cannot_abrir_caja(client_mesero):
    resp = client_mesero.post("/api/v1/caja/apertura", json={
        "turno": "manana",
        "monto_inicial": 100.0,
    })
    assert resp.status_code == 403


def test_cajero_can_reach_apertura_endpoint(client_cajero):
    resp = client_cajero.post("/api/v1/caja/apertura", json={
        "turno": "manana",
        "monto_inicial": 100.0,
    })
    assert resp.status_code != 403


# ── GET /caja/cierres — solo administrador ────────────────────────────────────

def test_cajero_cannot_ver_cierres(client_cajero):
    resp = client_cajero.get("/api/v1/caja/cierres")
    assert resp.status_code == 403


def test_mesero_cannot_ver_cierres(client_mesero):
    resp = client_mesero.get("/api/v1/caja/cierres")
    assert resp.status_code == 403


# ── POST /ventas — cajero y administrador únicamente ─────────────────────────

def test_mesero_cannot_registrar_venta(client_mesero):
    resp = client_mesero.post("/api/v1/ventas", json={
        "turno": "manana",
        "id_apertura": 1,
        "id_pedido": None,
        "id_cliente": None,
        "productos": [],
        "pagos": [],
    })
    assert resp.status_code == 403


def test_cajero_can_reach_venta_endpoint(client_cajero):
    resp = client_cajero.post("/api/v1/ventas", json={
        "turno": "manana",
        "id_apertura": 1,
        "id_pedido": None,
        "id_cliente": None,
        "productos": [],
        "pagos": [],
    })
    assert resp.status_code != 403


# ── PATCH /devoluciones/{id}/aprobar — solo administrador ────────────────────

def test_cajero_cannot_aprobar_devolucion(client_cajero):
    resp = client_cajero.patch("/api/v1/devoluciones/1/aprobar")
    assert resp.status_code == 403


def test_mesero_cannot_aprobar_devolucion(client_mesero):
    resp = client_mesero.patch("/api/v1/devoluciones/1/aprobar")
    assert resp.status_code == 403


def test_cajero_cannot_rechazar_devolucion(client_cajero):
    resp = client_cajero.patch("/api/v1/devoluciones/1/rechazar")
    assert resp.status_code == 403


# ── POST /recetas — solo administrador ───────────────────────────────────────

def test_cajero_cannot_crear_receta(client_cajero):
    resp = client_cajero.post("/api/v1/recetas", json={
        "id_producto": 1,
        "detalles_insumo": [],
        "detalles_subreceta": [],
        "pasos": [],
    })
    assert resp.status_code == 403


def test_mesero_cannot_crear_receta(client_mesero):
    resp = client_mesero.post("/api/v1/recetas", json={
        "id_producto": 1,
        "detalles_insumo": [],
        "detalles_subreceta": [],
        "pasos": [],
    })
    assert resp.status_code == 403


# ── PATCH /pedidos/{id}/estado — cajero, mesero y administrador ───────────────

def test_cajero_can_reach_cambiar_estado_pedido(client_cajero):
    _not_found = MajesaError("Pedido 999 no encontrado", 404)
    with patch("app.services.pedido_service.cambiar_estado_pedido",
               new=AsyncMock(side_effect=_not_found)):
        resp = client_cajero.patch("/api/v1/pedidos/999/estado?nuevo_estado=enviado")
    assert resp.status_code != 403


def test_mesero_can_reach_cambiar_estado_pedido(client_mesero):
    _not_found = MajesaError("Pedido 999 no encontrado", 404)
    with patch("app.services.pedido_service.cambiar_estado_pedido",
               new=AsyncMock(side_effect=_not_found)):
        resp = client_mesero.patch("/api/v1/pedidos/999/estado?nuevo_estado=enviado")
    assert resp.status_code != 403
