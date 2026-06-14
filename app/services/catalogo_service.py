"""
app/services/catalogo_service.py
Business logic for the base catalog modules of the POS system.
Author: charlykj
Issue: #38
"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalogo import Usuario
from app.repositories.catalogo_repo import (
    RolRepository, UsuarioRepository, ClienteRepository,
    MarcaRepository, UnidadMedidaRepository, ClasificacionRepository,
    CategoriaRepository, MetodoPagoRepository
)

# Roles que definen la jerarquía administrativa. Un "administrador" no
# puede gestionar (editar rol / eliminar) a otro usuario que tenga uno de
# estos roles; solo "super_admin" puede.
_ROLES_PROTEGIDOS = ("administrador", "super_admin")
_SUPER_ADMIN = "super_admin"

# Roles del sistema: no se pueden eliminar desde /roles porque
# require_rol() y la lógica de UsuarioService dependen de sus nombres.
_ROLES_DEL_SISTEMA = ("administrador", "super_admin")


def _rol_nombre(usuario: Usuario) -> str | None:
    return usuario.rol.nombre if usuario.rol else None


class RolService:
    def __init__(self, db: AsyncSession):
        self.repo = RolRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_rol: int):
        return await self.repo.get_by_id(id_rol)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_rol: int):
        rol = await self.repo.get_by_id(id_rol)
        if not rol:
            return False
        if rol.nombre in _ROLES_DEL_SISTEMA:
            raise HTTPException(
                status_code=400,
                detail=f"El rol '{rol.nombre}' es un rol del sistema y no puede eliminarse",
            )
        return await self.repo.delete(id_rol)


class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.repo = UsuarioRepository(db)
        self.rol_repo = RolRepository(db)

    async def listar(self, solo_activos: bool = False):
        return await self.repo.get_all(solo_activos=solo_activos)

    async def obtener(self, id_usuario: int):
        return await self.repo.get_by_id(id_usuario)

    async def crear(self, data, current_user: Usuario):
        if data.id_rol is not None:
            nuevo_rol = await self.rol_repo.get_by_id(data.id_rol)
            nuevo_rol_nombre = nuevo_rol.nombre if nuevo_rol else None
            if nuevo_rol_nombre == _SUPER_ADMIN and _rol_nombre(current_user) != _SUPER_ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Solo un super_admin puede asignar el rol 'super_admin'",
                )
        return await self.repo.create(data)

    async def actualizar(self, id_usuario: int, data, current_user: Usuario):
        target = await self.repo.get_by_id(id_usuario)
        if not target:
            return None

        current_rol_nombre = _rol_nombre(current_user)
        target_rol_nombre = _rol_nombre(target)

        if data.id_rol is not None and data.id_rol != target.id_rol:
            if id_usuario == current_user.id_usuario:
                raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")

            if target_rol_nombre in _ROLES_PROTEGIDOS and current_rol_nombre != _SUPER_ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Un administrador no puede cambiar el rol de otro administrador",
                )

            nuevo_rol = await self.rol_repo.get_by_id(data.id_rol)
            nuevo_rol_nombre = nuevo_rol.nombre if nuevo_rol else None
            if nuevo_rol_nombre == _SUPER_ADMIN and current_rol_nombre != _SUPER_ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail="Solo un super_admin puede asignar el rol 'super_admin'",
                )

        return await self.repo.update(id_usuario, data)

    async def eliminar(self, id_usuario: int, current_user: Usuario):
        target = await self.repo.get_by_id(id_usuario)
        if not target:
            return False

        if _rol_nombre(target) in _ROLES_PROTEGIDOS and _rol_nombre(current_user) != _SUPER_ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Un administrador no puede eliminar a otro administrador",
            )

        return await self.repo.delete(id_usuario)


class ClienteService:
    def __init__(self, db: AsyncSession):
        self.repo = ClienteRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_cliente: int):
        return await self.repo.get_by_id(id_cliente)

    async def crear(self, data):
        return await self.repo.create(data)

    async def actualizar(self, id_cliente: int, data):
        return await self.repo.update(id_cliente, data)

    async def eliminar(self, id_cliente: int):
        return await self.repo.delete(id_cliente)


class MarcaService:
    def __init__(self, db: AsyncSession):
        self.repo = MarcaRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_marca: int):
        return await self.repo.get_by_id(id_marca)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_marca: int):
        return await self.repo.delete(id_marca)


class UnidadMedidaService:
    def __init__(self, db: AsyncSession):
        self.repo = UnidadMedidaRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_unidad: int):
        return await self.repo.get_by_id(id_unidad)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_unidad: int):
        return await self.repo.delete(id_unidad)


class ClasificacionService:
    def __init__(self, db: AsyncSession):
        self.repo = ClasificacionRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_clasificacion: int):
        return await self.repo.get_by_id(id_clasificacion)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_clasificacion: int):
        return await self.repo.delete(id_clasificacion)


class CategoriaService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoriaRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_categoria: int):
        return await self.repo.get_by_id(id_categoria)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_categoria: int):
        return await self.repo.delete(id_categoria)


class MetodoPagoService:
    def __init__(self, db: AsyncSession):
        self.repo = MetodoPagoRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_metodo_pago: int):
        return await self.repo.get_by_id(id_metodo_pago)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_metodo_pago: int):
        return await self.repo.delete(id_metodo_pago)