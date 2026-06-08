"""
test_ajuste_inventario.py
Tests de integración para el módulo AjusteInventario.

Criterios que valida:
- GET /ajustes-inventario lista todos los ajustes.
- GET /ajustes-inventario/{id} retorna un ajuste específico.
- POST /ajustes-inventario crea un ajuste en estado pendiente.
- PATCH /aprobar: modifica stock, crea MovimientoInventario, cambia estado.
- PATCH /rechazar: NO modifica stock, cambia estado a rechazado.
- Aprobar/rechazar un ajuste no-pendiente → 400.
- Cantidad negativa al aprobar usa descontar_stock().
"""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_listar_ajustes(client, ajuste_pendiente):
    resp = await client.get("/api/v1/ajustes-inventario")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_obtener_ajuste_por_id(client, ajuste_pendiente):
    resp = await client.get(f"/api/v1/ajustes-inventario/{ajuste_pendiente}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id_ajuste"] == ajuste_pendiente
    assert data["estado"] == "pendiente"


@pytest.mark.asyncio
async def test_obtener_ajuste_inexistente(client):
    resp = await client.get("/api/v1/ajustes-inventario/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_crear_ajuste_pendiente(client, insumo_con_stock):
    payload = {
        "id_insumo": insumo_con_stock["id_insumo"],
        "cantidad": "5",
        "motivo": "Corrección de conteo físico",
    }
    resp = await client.post("/api/v1/ajustes-inventario", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "pendiente"
    assert data["id_insumo"] == insumo_con_stock["id_insumo"]
    assert float(data["cantidad"]) == 5.0


@pytest.mark.asyncio
async def test_crear_ajuste_insumo_inexistente(client):
    payload = {"id_insumo": 999999, "cantidad": "5", "motivo": "Test"}
    resp = await client.post("/api/v1/ajustes-inventario", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_aprobar_ajuste_positivo_modifica_stock(
    client, ajuste_pendiente, insumo_con_stock, db_session
):
    """
    Aprobar un ajuste con cantidad positiva debe sumar al stock.
    Stock inicial = 10, ajuste = 3 → stock final = 13.
    """
    id_insumo = insumo_con_stock["id_insumo"]

    resp = await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/aprobar", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "aprobado"
    assert data["fecha_resolucion"] is not None

    db_session.expire_all()  # forzar recarga desde BD

    r = await db_session.execute(
        text("SELECT cantidad FROM pos.stock WHERE id_insumo = :i"),
        {"i": id_insumo},
    )
    cantidad = float(r.scalar_one())
    assert cantidad == 13.0


@pytest.mark.asyncio
async def test_aprobar_ajuste_crea_movimiento_inventario(
    client, ajuste_pendiente, insumo_con_stock, db_session
):
    id_insumo = insumo_con_stock["id_insumo"]
    await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/aprobar", json={})

    db_session.expire_all()  # forzar recarga desde BD

    r = await db_session.execute(
        text(
            "SELECT tipo, cantidad_anterior, cantidad_nueva "
            "FROM pos.movimiento_inventario "
            "WHERE id_insumo = :i ORDER BY fecha DESC LIMIT 1"
        ),
        {"i": id_insumo},
    )
    row = r.fetchone()
    assert row is not None, "Debe existir un MovimientoInventario"
    assert row[0] == "entrada"
    assert float(row[1]) == 10.0
    assert float(row[2]) == 13.0


@pytest.mark.asyncio
async def test_aprobar_ajuste_negativo_descuenta_stock(
    client, insumo_con_stock, db_session, usuario
):
    """Cantidad negativa → descontar_stock(). Stock 10 - 3 = 7."""
    id_insumo = insumo_con_stock["id_insumo"]
    r = await db_session.execute(
        text(
            "INSERT INTO pos.ajuste_inventario "
            "(id_insumo, id_usuario_solicita, cantidad, motivo, estado, fecha_solicitud) "
            "VALUES (:i, :u, -3, 'Merma', 'pendiente', now()) "
            "RETURNING id_ajuste"
        ),
        {"i": id_insumo, "u": usuario},
    )
    id_ajuste = r.scalar_one()
    await db_session.commit()

    resp = await client.patch(f"/api/v1/ajustes-inventario/{id_ajuste}/aprobar", json={})
    assert resp.status_code == 200

    db_session.expire_all()  # forzar recarga desde BD

    r2 = await db_session.execute(
        text("SELECT cantidad FROM pos.stock WHERE id_insumo = :i"),
        {"i": id_insumo},
    )
    assert float(r2.scalar_one()) == 7.0


@pytest.mark.asyncio
async def test_rechazar_ajuste_no_modifica_stock(
    client, ajuste_pendiente, insumo_con_stock, db_session
):
    id_insumo = insumo_con_stock["id_insumo"]

    resp = await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/rechazar", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "rechazado"
    assert data["fecha_resolucion"] is not None

    db_session.expire_all()  # forzar recarga desde BD

    r = await db_session.execute(
        text("SELECT cantidad FROM pos.stock WHERE id_insumo = :i"),
        {"i": id_insumo},
    )
    assert float(r.scalar_one()) == 10.0  # sin cambios


@pytest.mark.asyncio
async def test_rechazar_ajuste_no_crea_movimiento(
    client, ajuste_pendiente, insumo_con_stock, db_session
):
    id_insumo = insumo_con_stock["id_insumo"]
    await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/rechazar", json={})

    db_session.expire_all()  # forzar recarga desde BD

    r = await db_session.execute(
        text(
            "SELECT COUNT(*) FROM pos.movimiento_inventario WHERE id_insumo = :i"
        ),
        {"i": id_insumo},
    )
    assert r.scalar_one() == 0


@pytest.mark.asyncio
async def test_aprobar_ajuste_ya_aprobado_retorna_400(client, ajuste_pendiente):
    await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/aprobar", json={})
    resp = await client.patch(
        f"/api/v1/ajustes-inventario/{ajuste_pendiente}/aprobar", json={}
    )
    assert resp.status_code == 400
    assert "pendiente" in resp.json()["error"].lower()


@pytest.mark.asyncio
async def test_rechazar_ajuste_ya_rechazado_retorna_400(client, ajuste_pendiente):
    await client.patch(f"/api/v1/ajustes-inventario/{ajuste_pendiente}/rechazar", json={})
    resp = await client.patch(
        f"/api/v1/ajustes-inventario/{ajuste_pendiente}/rechazar", json={}
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_filtrar_ajustes_por_estado(client, ajuste_pendiente):
    resp = await client.get("/api/v1/ajustes-inventario?estado=pendiente")
    assert resp.status_code == 200
    estados = {item["estado"] for item in resp.json()}
    assert estados <= {"pendiente"}