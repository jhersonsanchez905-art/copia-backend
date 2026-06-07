"""
conftest.py
Fixtures compartidas para todos los tests de integración.

Estrategia:
- Cada test obtiene su propia sesión de DB (sin rollback compartido).
- Al finalizar cada test se hace DELETE de los registros creados en esa sesión,
  usando una tabla de seguimiento por test.
- El cliente HTTP usa AsyncClient + ASGITransport (sin levantar servidor).
"""
import datetime
from typing import AsyncGenerator
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from app.main import app

# ── Motor de test ─────────────────────────────────────────────────────────────
_raw = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
_parsed = urlparse(_raw)
_query = parse_qs(_parsed.query)
_query.pop("sslmode", None)
_query.pop("channel_binding", None)
_clean_url = urlunparse(
    _parsed._replace(query=urlencode({k: v[0] for k, v in _query.items()}))
)

TEST_ENGINE = create_async_engine(
    _clean_url,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = sessionmaker(
    TEST_ENGINE, class_=AsyncSession, expire_on_commit=False
)


# ── Sesión de DB por test ─────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    session = TestSessionLocal()
    session._test_created: dict[str, list] = {}

    def track(table: str, id_val):
        session._test_created.setdefault(table, []).append(id_val)

    session.track = track
    try:
        yield session
    finally:
        await session.rollback()
        cleanup_order = [
            ("pos.movimiento_inventario", "id_movimiento"),
            ("pos.alerta_perecible",      "id_alerta_perecible"),
            ("pos.alerta",                "id_alerta"),
            ("pos.ajuste_inventario",     "id_ajuste"),
            ("pos.orden_compra_detalle",  "id_detalle"),
            ("pos.orden_compra",          "id_orden_compra"),
            ("pos.stock",                 "id_stock"),
            ("pos.insumo",                "id_insumo"),
            ("pos.proveedor",             "id_proveedor"),
        ]
        for table, pk in cleanup_order:
            ids = session._test_created.get(table, [])
            if ids:
                placeholders = ", ".join(str(i) for i in ids)
                try:
                    await session.execute(
                        text(f"DELETE FROM {table} WHERE {pk} IN ({placeholders})")
                    )
                except Exception:
                    pass
        await session.commit()
        await session.close()


# ── Cliente HTTP por test ─────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from app.middleware.auditoria import AuditoriaMiddleware
    app.middleware_stack = None
    original_middleware = app.user_middleware.copy()
    app.user_middleware = [
        m for m in app.user_middleware
        if not (hasattr(m, 'cls') and m.cls == AuditoriaMiddleware)
    ]
    app.build_middleware_stack()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.user_middleware = original_middleware
    app.middleware_stack = None
    app.build_middleware_stack()
    app.dependency_overrides.clear()


# ── Fixtures de datos ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def rol(db_session: AsyncSession):
    r = await db_session.execute(
        text("SELECT id_rol FROM pos.rol LIMIT 1")
    )
    row = r.fetchone()
    if row:
        return row[0]
    result = await db_session.execute(
        text("INSERT INTO pos.rol (nombre) VALUES ('Test') RETURNING id_rol")
    )
    id_rol = result.scalar_one()
    await db_session.commit()
    return id_rol


@pytest_asyncio.fixture()
async def usuario(db_session: AsyncSession, rol):
    r = await db_session.execute(
        text("SELECT id_usuario FROM pos.usuario WHERE id_usuario = 1 LIMIT 1")
    )
    if r.scalar_one_or_none():
        return 1
    result = await db_session.execute(
        text(
            "INSERT INTO pos.usuario (clerk_id, nombre, correo, id_rol, activo) "
            "VALUES ('test_clerk_id', 'Test User', 'test@test.com', :r, true) "
            "RETURNING id_usuario"
        ),
        {"r": rol},
    )
    id_usuario = result.scalar_one()
    await db_session.commit()
    return id_usuario


@pytest_asyncio.fixture()
async def unidad(db_session: AsyncSession):
    r = await db_session.execute(
        text("SELECT id_unidad FROM pos.unidad_medida WHERE abreviatura = 'kg' LIMIT 1")
    )
    row = r.fetchone()
    if row:
        return row[0]
    result = await db_session.execute(
        text(
            "INSERT INTO pos.unidad_medida (nombre, abreviatura) "
            "VALUES ('Kilogramo', 'kg') RETURNING id_unidad"
        )
    )
    id_unidad = result.scalar_one()
    await db_session.commit()
    return id_unidad


@pytest_asyncio.fixture()
async def clasificacion(db_session: AsyncSession):
    r = await db_session.execute(
        text("SELECT id_clasificacion FROM pos.clasificacion WHERE nombre = 'PruebaTest' LIMIT 1")
    )
    row = r.fetchone()
    if row:
        return row[0]
    result = await db_session.execute(
        text(
            "INSERT INTO pos.clasificacion (nombre) "
            "VALUES ('PruebaTest') RETURNING id_clasificacion"
        )
    )
    id_clas = result.scalar_one()
    await db_session.commit()
    return id_clas


@pytest_asyncio.fixture()
async def insumo_con_stock(db_session: AsyncSession, unidad, clasificacion, usuario):
    r = await db_session.execute(
        text(
            "INSERT INTO pos.insumo "
            "(nombre, id_unidad, id_clasificacion, umbral_minimo, stock_minimo, "
            " stock_maximo, cantidad_a_pedir, activo, fecha_creacion, fecha_actualizacion) "
            "VALUES ('Insumo Test ' || extract(epoch from now())::text, "
            ":u, :c, 2, 5, 100, 10, true, now(), now()) "
            "RETURNING id_insumo"
        ),
        {"u": unidad, "c": clasificacion},
    )
    id_insumo = r.scalar_one()
    db_session.track("pos.insumo", id_insumo)

    r2 = await db_session.execute(
        text(
            "INSERT INTO pos.stock (id_insumo, cantidad, semaforo) "
            "VALUES (:i, 10, 'verde') RETURNING id_stock"
        ),
        {"i": id_insumo},
    )
    id_stock = r2.scalar_one()
    db_session.track("pos.stock", id_stock)
    await db_session.commit()
    return {"id_insumo": id_insumo, "id_stock": id_stock}


@pytest_asyncio.fixture()
async def insumo_stock_critico(db_session: AsyncSession, unidad, clasificacion):
    r = await db_session.execute(
        text(
            "INSERT INTO pos.insumo "
            "(nombre, id_unidad, id_clasificacion, umbral_minimo, stock_minimo, activo, fecha_creacion, fecha_actualizacion) "
            "VALUES ('Insumo Critico ' || extract(epoch from now())::text, :u, :c, 5, 10, true, now(), now()) "
            "RETURNING id_insumo"
        ),
        {"u": unidad, "c": clasificacion},
    )
    id_insumo = r.scalar_one()
    db_session.track("pos.insumo", id_insumo)

    r2 = await db_session.execute(
        text("INSERT INTO pos.stock (id_insumo, cantidad, semaforo) VALUES (:i, 1, 'rojo') RETURNING id_stock"),
        {"i": id_insumo},
    )
    db_session.track("pos.stock", r2.scalar_one())
    await db_session.commit()
    return id_insumo


@pytest_asyncio.fixture()
async def insumo_stock_vigilancia(db_session: AsyncSession, unidad, clasificacion):
    r = await db_session.execute(
        text(
            "INSERT INTO pos.insumo "
            "(nombre, id_unidad, id_clasificacion, umbral_minimo, stock_minimo, activo, fecha_creacion, fecha_actualizacion) "
            "VALUES ('Insumo Vigilancia ' || extract(epoch from now())::text, :u, :c, 2, 10, true, now(), now()) "
            "RETURNING id_insumo"
        ),
        {"u": unidad, "c": clasificacion},
    )
    id_insumo = r.scalar_one()
    db_session.track("pos.insumo", id_insumo)

    r2 = await db_session.execute(
        text("INSERT INTO pos.stock (id_insumo, cantidad, semaforo) VALUES (:i, 7, 'amarillo') RETURNING id_stock"),
        {"i": id_insumo},
    )
    db_session.track("pos.stock", r2.scalar_one())
    await db_session.commit()
    return id_insumo


@pytest_asyncio.fixture
async def ajuste_pendiente(db_session, insumo_con_stock, usuario):
    r = await db_session.execute(
        text(
            "INSERT INTO pos.ajuste_inventario "
            "(id_insumo, id_usuario_solicita, cantidad, motivo, estado, fecha_solicitud) "
            "VALUES (:i, :u, 3, 'Test fixture', 'pendiente', now()) "
            "RETURNING id_ajuste"
        ),
        {"i": insumo_con_stock["id_insumo"], "u": usuario},
    )
    id_ajuste = r.scalar_one()
    await db_session.commit()
    return id_ajuste


@pytest_asyncio.fixture()
async def proveedor(db_session: AsyncSession):
    r = await db_session.execute(
        text(
            "INSERT INTO pos.proveedor (nombre, activo) "
            "VALUES ('Proveedor Test ' || extract(epoch from now())::text, true) "
            "RETURNING id_proveedor"
        )
    )
    id_proveedor = r.scalar_one()
    db_session.track("pos.proveedor", id_proveedor)
    await db_session.commit()
    return id_proveedor


@pytest_asyncio.fixture()
async def orden_borrador(db_session: AsyncSession, proveedor, insumo_con_stock, usuario):
    id_insumo = insumo_con_stock["id_insumo"]
    r = await db_session.execute(
        text(
            "INSERT INTO pos.orden_compra "
            "(id_proveedor, id_usuario, numero_orden, estado, subtotal, impuestos, total, "
            " fecha_creacion, fecha_actualizacion) "        # ← agregar
            "VALUES (:p, :u, 'OC-TEST-' || extract(epoch from now())::text, "
            "'borrador', 0, 0, 0, now(), now()) "           # ← agregar
            "RETURNING id_orden_compra"
        ),
        {"p": proveedor, "u": usuario},
    )
    id_orden = r.scalar_one()
    db_session.track("pos.orden_compra", id_orden)

    r2 = await db_session.execute(
        text(
            "INSERT INTO pos.orden_compra_detalle "
            "(id_orden_compra, id_insumo, cantidad_solicitada, cantidad_recibida, "
            " precio_unitario, subtotal_linea, fecha_creacion, fecha_actualizacion) "   # ← agregar
            "VALUES (:o, :i, 20, 0, 5.00, 100.00, now(), now()) "                       # ← agregar
            "RETURNING id_detalle"
        ),
        {"o": id_orden, "i": id_insumo},
    )
    db_session.track("pos.orden_compra_detalle", r2.scalar_one())
    await db_session.commit()
    return {"id_orden": id_orden, "id_insumo": id_insumo}


@pytest_asyncio.fixture()
async def orden_enviada(db_session: AsyncSession, orden_borrador):
    await db_session.execute(
        text("UPDATE pos.orden_compra SET estado = 'enviada' WHERE id_orden_compra = :o"),
        {"o": orden_borrador["id_orden"]},
    )
    await db_session.commit()
    return orden_borrador


@pytest_asyncio.fixture()
async def alerta_perecible_activa(db_session: AsyncSession, insumo_con_stock):
    id_insumo = insumo_con_stock["id_insumo"]
    id_stock = insumo_con_stock["id_stock"]
    hoy = datetime.date.today()
    r = await db_session.execute(
        text(
            "INSERT INTO pos.alerta_perecible "
            "(id_insumo, id_stock, fecha_ingreso, dias_en_inventario, estado, fecha_creacion) "
            "VALUES (:i, :s, :f, 10, 'activa', now()) "
            "RETURNING id_alerta_perecible"
        ),
        {"i": id_insumo, "s": id_stock, "f": hoy},
    )
    id_alerta = r.scalar_one()
    db_session.track("pos.alerta_perecible", id_alerta)
    await db_session.commit()
    return id_alerta