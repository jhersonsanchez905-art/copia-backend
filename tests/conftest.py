"""
Shared fixtures for all tests.
Overrides get_db and get_current_user so no real DB or Clerk calls happen.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.main import app
from app.models.catalogo import Rol, Usuario


def _make_user(rol_nombre: str, id_usuario: int = 1) -> Usuario:
    rol = Rol(id_rol=1, nombre=rol_nombre)
    user = Usuario(
        id_usuario=id_usuario,
        clerk_id="clerk_test_xyz",
        nombre="Test User",
        correo="test@majesa.com",
        id_rol=1,
        activo=True,
    )
    user.rol = rol
    user.fecha_creacion = datetime.now(timezone.utc)
    return user


@pytest.fixture
def db_mock():
    return AsyncMock()


@pytest.fixture
def admin_user():
    return _make_user("administrador")


@pytest.fixture
def cajero_user():
    return _make_user("cajero")


@pytest.fixture
def mesero_user():
    return _make_user("mesero")


def _setup_client(user: Usuario, db: AsyncMock) -> TestClient:
    async def _db():
        yield db

    async def _get_user():
        return user

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = _get_user
    return TestClient(app)


@pytest.fixture
def client_admin(admin_user, db_mock):
    client = _setup_client(admin_user, db_mock)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_cajero(cajero_user, db_mock):
    client = _setup_client(cajero_user, db_mock)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_mesero(mesero_user, db_mock):
    client = _setup_client(mesero_user, db_mock)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth(db_mock):
    async def _db():
        yield db_mock

    async def _no_auth():
        raise HTTPException(status_code=401, detail="Token de autorización requerido")

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = _no_auth
    yield TestClient(app)
    app.dependency_overrides.clear()
