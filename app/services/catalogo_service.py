"""
app/services/catalogo_service.py
Business logic for the base catalog modules of the POS system.
Author: charlykj
Issue: #38
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.catalogo_repo import (
    RolRepository, UsuarioRepository, ClienteRepository,
    MarcaRepository, UnidadMedidaRepository, ClasificacionRepository,
    CategoriaRepository, MetodoPagoRepository
)


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
        return await self.repo.delete(id_rol)


class UsuarioService:
    def __init__(self, db: AsyncSession):
        self.repo = UsuarioRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_usuario: int):
        return await self.repo.get_by_id(id_usuario)

    async def crear(self, data):
        return await self.repo.create(data)

    async def actualizar(self, id_usuario: int, data):
        return await self.repo.update(id_usuario, data)

    async def eliminar(self, id_usuario: int):
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