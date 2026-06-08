"""
test_orden_compra.py
Tests de integración para el módulo OrdenCompra.

Criterios que valida:
- GET /ordenes-compra lista órdenes.
- GET /ordenes-compra/{id} retorna una orden específica.
- POST /ordenes-compra crea en estado borrador.
- PATCH /enviar: borrador → enviada.
- PATCH /cancelar: borrador → cancelada y enviada → cancelada.
- PATCH /recibir: enviada → recibida, actualiza stock, crea MovimientoInventario.
- Transiciones inválidas retornan HTTP 400 con mensaje descriptivo.
- Recibir una orden no modifica stock directamente (pasa por inventario_service).
"""
import pytest
from sqlalchemy import text
import time


@pytest.mark.asyncio
async def test_listar_ordenes_compra(client, orden_borrador):
    resp = await client.get("/api/v1/ordenes-compra")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_obtener_orden_por_id(client, orden_borrador):
    id_orden = orden_borrador["id_orden"]
    resp = await client.get(f"/api/v1/ordenes-compra/{id_orden}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_orden_compra"] == id_orden
    assert data["estado"] == "borrador"


@pytest.mark.asyncio
async def test_obtener_orden_inexistente(client):
    resp = await client.get("/api/v1/ordenes-compra/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_crear_orden_compra(client, proveedor, insumo_con_stock, usuario):
    payload = {
        "id_proveedor": proveedor,
        "id_usuario": usuario,
        "numero_orden": f"OC-PYTEST-{int(time.time())}",
        "detalles": [
            {
                "id_insumo": insumo_con_stock["id_insumo"],
                "cantidad_solicitada": "15",
                "precio_unitario": "3.50",
            }
        ],
    }
    resp = await client.post("/api/v1/ordenes-compra", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "borrador"
    assert data["numero_orden"] == payload["numero_orden"]
    assert len(data["detalles"]) == 1


@pytest.mark.asyncio
async def test_enviar_orden(client, orden_borrador):
    id_orden = orden_borrador["id_orden"]
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/enviar")
    assert resp.status_code == 200
    assert resp.json()["estado"] == "enviada"


@pytest.mark.asyncio
async def test_cancelar_orden_desde_borrador(client, orden_borrador):
    id_orden = orden_borrador["id_orden"]
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/cancelar")
    assert resp.status_code == 200
    assert resp.json()["estado"] == "cancelada"


@pytest.mark.asyncio
async def test_cancelar_orden_desde_enviada(client, orden_enviada):
    id_orden = orden_enviada["id_orden"]
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/cancelar")
    assert resp.status_code == 200
    assert resp.json()["estado"] == "cancelada"


@pytest.mark.asyncio
async def test_transicion_invalida_borrador_a_recibida_retorna_400(client, orden_borrador):
    id_orden = orden_borrador["id_orden"]
    payload = {"detalles": []}
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)
    assert resp.status_code == 400
    error = resp.json()["error"]
    assert "borrador" in error.lower() or "inválida" in error.lower() or "invalida" in error.lower()


@pytest.mark.asyncio
async def test_transicion_invalida_cancelada_a_enviada_retorna_400(client, orden_borrador):
    id_orden = orden_borrador["id_orden"]
    await client.patch(f"/api/v1/ordenes-compra/{id_orden}/cancelar")
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/enviar")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_transicion_invalida_recibida_a_cancelada_retorna_400(
    client, orden_enviada, db_session
):
    id_orden = orden_enviada["id_orden"]
    id_insumo = orden_enviada["id_insumo"]
    payload = {"detalles": [{"id_insumo": id_insumo, "cantidad_recibida": "20"}]}
    await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/cancelar")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_recibir_orden_actualiza_stock(client, orden_enviada, db_session):
    """
    Stock inicial = 10. Se reciben 20 unidades → stock final = 30.
    """
    id_orden = orden_enviada["id_orden"]
    id_insumo = orden_enviada["id_insumo"]

    payload = {"detalles": [{"id_insumo": id_insumo, "cantidad_recibida": "20"}]}
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "recibida"

    r = await db_session.execute(
        text("SELECT cantidad FROM pos.stock WHERE id_insumo = :i"),
        {"i": id_insumo},
    )
    assert float(r.scalar_one()) == 30.0


@pytest.mark.asyncio
async def test_recibir_orden_crea_movimiento_inventario(
    client, orden_enviada, db_session
):
    id_orden = orden_enviada["id_orden"]
    id_insumo = orden_enviada["id_insumo"]

    payload = {"detalles": [{"id_insumo": id_insumo, "cantidad_recibida": "20"}]}
    await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)

    r = await db_session.execute(
        text(
            "SELECT tipo, id_orden_compra, cantidad "
            "FROM pos.movimiento_inventario "
            "WHERE id_insumo = :i ORDER BY fecha DESC LIMIT 1"
        ),
        {"i": id_insumo},
    )
    row = r.fetchone()
    assert row is not None, "Debe existir un MovimientoInventario"
    assert row[0] == "entrada"
    assert row[1] == id_orden
    assert float(row[2]) == 20.0


@pytest.mark.asyncio
async def test_recibir_orden_actualiza_cantidad_recibida_detalle(
    client, orden_enviada, db_session
):
    id_orden = orden_enviada["id_orden"]
    id_insumo = orden_enviada["id_insumo"]

    payload = {"detalles": [{"id_insumo": id_insumo, "cantidad_recibida": "20"}]}
    await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)

    r = await db_session.execute(
        text(
            "SELECT cantidad_recibida FROM pos.orden_compra_detalle "
            "WHERE id_orden_compra = :o AND id_insumo = :i"
        ),
        {"o": id_orden, "i": id_insumo},
    )
    assert float(r.scalar_one()) == 20.0


@pytest.mark.asyncio
async def test_recibir_orden_con_insumo_inexistente_retorna_400(
    client, orden_enviada
):
    id_orden = orden_enviada["id_orden"]
    payload = {"detalles": [{"id_insumo": 999999, "cantidad_recibida": "5"}]}
    resp = await client.patch(f"/api/v1/ordenes-compra/{id_orden}/recibir", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_filtrar_ordenes_por_estado(client, orden_borrador):
    resp = await client.get("/api/v1/ordenes-compra?estado=borrador")
    assert resp.status_code == 200
    estados = {o["estado"] for o in resp.json()}
    assert estados <= {"borrador"}