"""
Unit tests for UsuarioService / RolService role-management validations:
- super_admin tiene acceso total (probado vía require_rol en test_auth_roles.py)
- un administrador no puede eliminar ni cambiar el rol de otro administrador/super_admin
- solo super_admin puede asignar el rol 'super_admin'
- nadie puede cambiar su propio rol
- los roles 'administrador' y 'super_admin' no se pueden eliminar desde /roles
No real DB — los repositorios se mockean con AsyncMock.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.catalogo import Rol, Usuario
from app.schemas.catalogo_schema import UsuarioCreate, UsuarioUpdate
from app.services.catalogo_service import RolService, UsuarioService


def _usuario(id_usuario: int, rol_nombre: str | None, id_rol: int | None = 1) -> Usuario:
    user = Usuario(id_usuario=id_usuario, clerk_id=f"clerk_{id_usuario}", nombre="N", correo="n@x.com", id_rol=id_rol, activo=True)
    user.rol = Rol(id_rol=id_rol, nombre=rol_nombre) if rol_nombre else None
    return user


def _rol(id_rol: int, nombre: str) -> Rol:
    return Rol(id_rol=id_rol, nombre=nombre)


@pytest.fixture
def patched_repos():
    usuario_repo = AsyncMock()
    rol_repo = AsyncMock()
    with patch("app.services.catalogo_service.UsuarioRepository", return_value=usuario_repo), \
         patch("app.services.catalogo_service.RolRepository", return_value=rol_repo):
        yield usuario_repo, rol_repo


@pytest.mark.asyncio
class TestEliminarUsuario:
    async def test_admin_no_puede_eliminar_a_otro_admin(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        otro_admin = _usuario(2, "administrador")
        usuario_repo.get_by_id.return_value = otro_admin

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).eliminar(2, admin)

        assert exc.value.status_code == 403
        usuario_repo.delete.assert_not_called()

    async def test_admin_no_puede_eliminar_a_super_admin(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        super_admin = _usuario(3, "super_admin")
        usuario_repo.get_by_id.return_value = super_admin

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).eliminar(3, admin)

        assert exc.value.status_code == 403

    async def test_admin_puede_eliminar_a_un_cajero(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        cajero = _usuario(4, "cajero")
        usuario_repo.get_by_id.return_value = cajero
        usuario_repo.delete.return_value = True

        result = await UsuarioService(AsyncMock()).eliminar(4, admin)

        assert result is True
        usuario_repo.delete.assert_awaited_once_with(4)

    async def test_super_admin_puede_eliminar_a_un_admin(self, patched_repos):
        usuario_repo, _ = patched_repos
        super_admin = _usuario(2, "super_admin")
        admin = _usuario(1, "administrador")
        usuario_repo.get_by_id.return_value = admin
        usuario_repo.delete.return_value = True

        result = await UsuarioService(AsyncMock()).eliminar(1, super_admin)

        assert result is True

    async def test_usuario_no_encontrado_retorna_false(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        usuario_repo.get_by_id.return_value = None

        result = await UsuarioService(AsyncMock()).eliminar(999, admin)

        assert result is False


@pytest.mark.asyncio
class TestActualizarUsuarioRol:
    async def test_no_puedes_cambiar_tu_propio_rol(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador", id_rol=1)
        usuario_repo.get_by_id.return_value = admin

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).actualizar(1, UsuarioUpdate(id_rol=2), admin)

        assert exc.value.status_code == 400

    async def test_admin_no_puede_cambiar_rol_de_otro_admin(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        otro_admin = _usuario(2, "administrador", id_rol=1)
        usuario_repo.get_by_id.return_value = otro_admin

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).actualizar(2, UsuarioUpdate(id_rol=3), admin)

        assert exc.value.status_code == 403

    async def test_admin_no_puede_asignar_rol_super_admin(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        admin = _usuario(1, "administrador")
        cajero = _usuario(4, "cajero", id_rol=3)
        usuario_repo.get_by_id.return_value = cajero
        rol_repo.get_by_id.return_value = _rol(99, "super_admin")

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).actualizar(4, UsuarioUpdate(id_rol=99), admin)

        assert exc.value.status_code == 403

    async def test_admin_puede_cambiar_rol_de_un_cajero(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        admin = _usuario(1, "administrador")
        cajero = _usuario(4, "cajero", id_rol=3)
        usuario_repo.get_by_id.return_value = cajero
        rol_repo.get_by_id.return_value = _rol(5, "mesero")
        usuario_repo.update.return_value = cajero

        result = await UsuarioService(AsyncMock()).actualizar(4, UsuarioUpdate(id_rol=5), admin)

        assert result is cajero
        usuario_repo.update.assert_awaited_once()

    async def test_super_admin_puede_cambiar_rol_de_un_admin(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        super_admin = _usuario(2, "super_admin")
        admin = _usuario(1, "administrador", id_rol=1)
        usuario_repo.get_by_id.return_value = admin
        rol_repo.get_by_id.return_value = _rol(3, "cajero")
        usuario_repo.update.return_value = admin

        result = await UsuarioService(AsyncMock()).actualizar(1, UsuarioUpdate(id_rol=3), super_admin)

        assert result is admin

    async def test_super_admin_puede_asignar_rol_super_admin(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        super_admin = _usuario(2, "super_admin")
        cajero = _usuario(4, "cajero", id_rol=3)
        usuario_repo.get_by_id.return_value = cajero
        rol_repo.get_by_id.return_value = _rol(99, "super_admin")
        usuario_repo.update.return_value = cajero

        result = await UsuarioService(AsyncMock()).actualizar(4, UsuarioUpdate(id_rol=99), super_admin)

        assert result is cajero

    async def test_actualizar_sin_cambio_de_rol_no_valida_jerarquia(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        otro_admin = _usuario(2, "administrador", id_rol=1)
        usuario_repo.get_by_id.return_value = otro_admin
        usuario_repo.update.return_value = otro_admin

        result = await UsuarioService(AsyncMock()).actualizar(2, UsuarioUpdate(nombre="Nuevo nombre"), admin)

        assert result is otro_admin

    async def test_usuario_no_encontrado_retorna_none(self, patched_repos):
        usuario_repo, _ = patched_repos
        admin = _usuario(1, "administrador")
        usuario_repo.get_by_id.return_value = None

        result = await UsuarioService(AsyncMock()).actualizar(999, UsuarioUpdate(nombre="X"), admin)

        assert result is None


@pytest.mark.asyncio
class TestCrearUsuario:
    async def test_admin_no_puede_crear_usuario_super_admin(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        admin = _usuario(1, "administrador")
        rol_repo.get_by_id.return_value = _rol(99, "super_admin")

        with pytest.raises(HTTPException) as exc:
            await UsuarioService(AsyncMock()).crear(
                UsuarioCreate(clerk_id="user_x", nombre="X", correo="x@x.com", id_rol=99), admin
            )

        assert exc.value.status_code == 403
        usuario_repo.create.assert_not_called()

    async def test_super_admin_puede_crear_usuario_super_admin(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        super_admin = _usuario(2, "super_admin")
        rol_repo.get_by_id.return_value = _rol(99, "super_admin")
        usuario_repo.create.return_value = MagicMock()

        await UsuarioService(AsyncMock()).crear(
            UsuarioCreate(clerk_id="user_x", nombre="X", correo="x@x.com", id_rol=99), super_admin
        )

        usuario_repo.create.assert_awaited_once()

    async def test_admin_puede_crear_usuario_cajero(self, patched_repos):
        usuario_repo, rol_repo = patched_repos
        admin = _usuario(1, "administrador")
        rol_repo.get_by_id.return_value = _rol(3, "cajero")
        usuario_repo.create.return_value = MagicMock()

        await UsuarioService(AsyncMock()).crear(
            UsuarioCreate(clerk_id="user_x", nombre="X", correo="x@x.com", id_rol=3), admin
        )

        usuario_repo.create.assert_awaited_once()


@pytest.mark.asyncio
class TestEliminarRol:
    async def test_no_se_puede_eliminar_rol_administrador(self, patched_repos):
        _, rol_repo = patched_repos
        rol_repo.get_by_id.return_value = _rol(1, "administrador")

        with pytest.raises(HTTPException) as exc:
            await RolService(AsyncMock()).eliminar(1)

        assert exc.value.status_code == 400
        rol_repo.delete.assert_not_called()

    async def test_no_se_puede_eliminar_rol_super_admin(self, patched_repos):
        _, rol_repo = patched_repos
        rol_repo.get_by_id.return_value = _rol(99, "super_admin")

        with pytest.raises(HTTPException) as exc:
            await RolService(AsyncMock()).eliminar(99)

        assert exc.value.status_code == 400

    async def test_se_puede_eliminar_rol_cajero(self, patched_repos):
        _, rol_repo = patched_repos
        rol_repo.get_by_id.return_value = _rol(3, "cajero")
        rol_repo.delete.return_value = True

        result = await RolService(AsyncMock()).eliminar(3)

        assert result is True
        rol_repo.delete.assert_awaited_once_with(3)

    async def test_rol_no_encontrado_retorna_false(self, patched_repos):
        _, rol_repo = patched_repos
        rol_repo.get_by_id.return_value = None

        result = await RolService(AsyncMock()).eliminar(404)

        assert result is False
