"""
test_alerta_perecible.py
Tests de integración para el módulo AlertaPerecible.

Criterios que valida:
- GET /alertas-perecibles lista alertas.
- GET /alertas-perecibles/{id} retorna una alerta específica.
- PATCH /resolver cambia estado a 'resuelta'.
- Resolver una alerta ya resuelta → 400.
- No existe endpoint POST.
"""
import pytest


@pytest.mark.asyncio
async def test_listar_alertas_perecibles(client, alerta_perecible_activa):
    resp = await client.get("/api/v1/alertas-perecibles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    ids = [a["id_alerta_perecible"] for a in resp.json()]
    assert alerta_perecible_activa in ids


@pytest.mark.asyncio
async def test_obtener_alerta_por_id(client, alerta_perecible_activa):
    resp = await client.get(f"/api/v1/alertas-perecibles/{alerta_perecible_activa}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_alerta_perecible"] == alerta_perecible_activa
    assert data["estado"] == "activa"


@pytest.mark.asyncio
async def test_obtener_alerta_inexistente(client):
    resp = await client.get("/api/v1/alertas-perecibles/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resolver_alerta(client, alerta_perecible_activa):
    resp = await client.patch(f"/api/v1/alertas-perecibles/{alerta_perecible_activa}/resolver")
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "resuelta"
    assert data["fecha_resolucion"] is not None


@pytest.mark.asyncio
async def test_resolver_alerta_ya_resuelta_retorna_400(client, alerta_perecible_activa):
    await client.patch(f"/api/v1/alertas-perecibles/{alerta_perecible_activa}/resolver")
    resp = await client.patch(
        f"/api/v1/alertas-perecibles/{alerta_perecible_activa}/resolver"
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_no_existe_post_alerta_perecible(client):
    """Las alertas son generadas automáticamente — no debe existir POST."""
    resp = await client.post("/api/v1/alertas-perecibles", json={})
    assert resp.status_code == 405


@pytest.mark.asyncio
async def test_filtrar_alertas_por_estado_activa(client, alerta_perecible_activa):
    resp = await client.get("/api/v1/alertas-perecibles?estado=activa")
    assert resp.status_code == 200
    estados = {a["estado"] for a in resp.json()}
    assert estados <= {"activa"}


@pytest.mark.asyncio
async def test_schema_alerta_perecible(client, alerta_perecible_activa):
    resp = await client.get(f"/api/v1/alertas-perecibles/{alerta_perecible_activa}")
    data = resp.json()
    campos_requeridos = {
        "id_alerta_perecible", "id_insumo", "id_stock",
        "fecha_ingreso", "dias_en_inventario", "estado", "fecha_creacion",
    }
    assert campos_requeridos <= set(data.keys())