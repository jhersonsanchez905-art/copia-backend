"""
Integration tests for the /recetas endpoints.
Focuses on the no-filter listing endpoint used by the frontend product table.
"""
from unittest.mock import AsyncMock, patch

from app.exceptions import MajesaError


# ── GET /recetas — listar todas ───────────────────────────────────────────────

def test_listar_recetas_returns_200(client_admin):
    with patch(
        "app.services.receta_service.listar_todas_las_versiones",
        new=AsyncMock(return_value=[]),
    ):
        resp = client_admin.get("/api/v1/recetas")
    assert resp.status_code == 200


def test_listar_recetas_returns_list(client_admin):
    with patch(
        "app.services.receta_service.listar_todas_las_versiones",
        new=AsyncMock(return_value=[]),
    ):
        data = client_admin.get("/api/v1/recetas").json()
    assert isinstance(data, list)


def test_listar_recetas_requires_auth(client_no_auth):
    resp = client_no_auth.get("/api/v1/recetas")
    assert resp.status_code == 401


def test_listar_recetas_pagination_skip_limit(client_admin):
    with patch(
        "app.services.receta_service.listar_todas_las_versiones",
        new=AsyncMock(return_value=[]),
    ) as mock:
        resp = client_admin.get("/api/v1/recetas?skip=10&limit=5")
        assert resp.status_code == 200
        _, kwargs = mock.call_args
        assert kwargs.get("skip") == 10
        assert kwargs.get("limit") == 5


def test_listar_recetas_default_pagination(client_admin):
    with patch(
        "app.services.receta_service.listar_todas_las_versiones",
        new=AsyncMock(return_value=[]),
    ) as mock:
        client_admin.get("/api/v1/recetas")
        _, kwargs = mock.call_args
        assert kwargs.get("skip") == 0
        assert kwargs.get("limit") == 50


def test_listar_recetas_solo_vigente_flag(client_admin):
    with patch(
        "app.services.receta_service.listar_todas_las_versiones",
        new=AsyncMock(return_value=[]),
    ) as mock:
        client_admin.get("/api/v1/recetas?solo_vigente=true")
        _, kwargs = mock.call_args
        assert kwargs.get("solo_vigente") is True


def test_listar_recetas_limit_invalid_returns_422(client_admin):
    resp = client_admin.get("/api/v1/recetas?limit=0")
    assert resp.status_code == 422


def test_listar_recetas_skip_negative_returns_422(client_admin):
    resp = client_admin.get("/api/v1/recetas?skip=-1")
    assert resp.status_code == 422


# ── GET /recetas/{version_id} ─────────────────────────────────────────────────

def test_obtener_receta_not_found_returns_404(client_admin):
    with patch(
        "app.services.receta_service.obtener_version",
        new=AsyncMock(side_effect=MajesaError("RecetaVersion 999 no encontrada", 404)),
    ):
        resp = client_admin.get("/api/v1/recetas/999")
    assert resp.status_code == 404


def test_obtener_receta_requires_auth(client_no_auth):
    resp = client_no_auth.get("/api/v1/recetas/1")
    assert resp.status_code == 401


# ── POST /recetas — solo administrador ───────────────────────────────────────

def test_crear_receta_missing_id_producto_returns_422(client_admin):
    resp = client_admin.post("/api/v1/recetas", json={
        "detalles_insumo": [],
        "detalles_subreceta": [],
        "pasos": [],
    })
    assert resp.status_code == 422


def test_crear_receta_cajero_blocked_returns_403(client_cajero):
    resp = client_cajero.post("/api/v1/recetas", json={
        "id_producto": 1,
        "detalles_insumo": [],
        "detalles_subreceta": [],
        "pasos": [],
    })
    assert resp.status_code == 403
