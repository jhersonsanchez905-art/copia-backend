"""
Unit tests for require_rol(): super_admin must bypass any role restriction.
"""
import pytest
from fastapi import HTTPException

from app.dependencies.roles import require_rol
from app.models.catalogo import Rol, Usuario


def _usuario(rol_nombre: str | None) -> Usuario:
    user = Usuario(id_usuario=1, clerk_id="clerk_1", nombre="N", correo="n@x.com", id_rol=1, activo=True)
    user.rol = Rol(id_rol=1, nombre=rol_nombre) if rol_nombre else None
    return user


@pytest.mark.asyncio
async def test_super_admin_bypasses_any_role_requirement():
    check = require_rol("administrador")
    user = _usuario("super_admin")

    result = await check(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_administrador_allowed_when_required():
    check = require_rol("administrador")
    user = _usuario("administrador")

    result = await check(current_user=user)

    assert result is user


@pytest.mark.asyncio
async def test_cajero_rejected_when_administrador_required():
    check = require_rol("administrador")
    user = _usuario("cajero")

    with pytest.raises(HTTPException) as exc:
        await check(current_user=user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_no_rol_rejected():
    check = require_rol("administrador")
    user = _usuario(None)

    with pytest.raises(HTTPException) as exc:
        await check(current_user=user)

    assert exc.value.status_code == 403
