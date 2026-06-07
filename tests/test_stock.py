"""
test_stock.py
Tests de integración para GET /stock — módulo de solo consulta.

Criterios que valida:
- GET /stock retorna lista con semáforo incluido.
- GET /stock/{id_insumo} retorna el stock de un insumo específico.
- GET /stock/criticos retorna ÚNICAMENTE semáforo rojo.
- GET /stock/vigilancia retorna ÚNICAMENTE semáforo amarillo.
- GET /stock/{id_insumo} con ID inexistente → 404.
"""
import pytest


@pytest.mark.asyncio
async def test_listar_stock(client, insumo_con_stock):
    resp = await client.get("/api/v1/stock")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids = [item["id_insumo"] for item in data]
    assert insumo_con_stock["id_insumo"] in ids


@pytest.mark.asyncio
async def test_listar_stock_respeta_schema(client, insumo_con_stock):
    resp = await client.get("/api/v1/stock")
    assert resp.status_code == 200
    item = next(
        (i for i in resp.json() if i["id_insumo"] == insumo_con_stock["id_insumo"]),
        None,
    )
    assert item is not None
    assert "id_stock" in item
    assert "cantidad" in item
    assert "semaforo" in item
    assert item["semaforo"] in ("verde", "amarillo", "rojo")


@pytest.mark.asyncio
async def test_get_stock_por_insumo(client, insumo_con_stock):
    id_insumo = insumo_con_stock["id_insumo"]
    resp = await client.get(f"/api/v1/stock/{id_insumo}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_insumo"] == id_insumo
    assert float(data["cantidad"]) == 10.0
    assert data["semaforo"] == "verde"


@pytest.mark.asyncio
async def test_get_stock_insumo_inexistente(client):
    resp = await client.get("/api/v1/stock/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stock_criticos_solo_rojo(client, insumo_stock_critico, insumo_con_stock):
    resp = await client.get("/api/v1/stock/criticos")
    assert resp.status_code == 200
    data = resp.json()
    semaforos = {item["semaforo"] for item in data}
    # Solo debe haber rojo — ningún verde ni amarillo
    assert semaforos <= {"rojo"}, f"Se esperaba solo 'rojo', se obtuvo: {semaforos}"
    ids = [item["id_insumo"] for item in data]
    assert insumo_stock_critico in ids
    assert insumo_con_stock["id_insumo"] not in ids


@pytest.mark.asyncio
async def test_stock_vigilancia_solo_amarillo(client, insumo_stock_vigilancia, insumo_con_stock):
    resp = await client.get("/api/v1/stock/vigilancia")
    assert resp.status_code == 200
    data = resp.json()
    semaforos = {item["semaforo"] for item in data}
    assert semaforos <= {"amarillo"}, f"Se esperaba solo 'amarillo', se obtuvo: {semaforos}"
    ids = [item["id_insumo"] for item in data]
    assert insumo_stock_vigilancia in ids
    assert insumo_con_stock["id_insumo"] not in ids


@pytest.mark.asyncio
async def test_no_existe_post_stock(client):
    """El módulo stock no debe aceptar POST."""
    resp = await client.post("/api/v1/stock", json={})
    assert resp.status_code in (404, 405)


@pytest.mark.asyncio
async def test_no_existe_put_stock(client, insumo_con_stock):
    """El módulo stock no debe aceptar PUT."""
    id_insumo = insumo_con_stock["id_insumo"]
    resp = await client.put(f"/api/v1/stock/{id_insumo}", json={"cantidad": 999})
    assert resp.status_code in (404, 405)