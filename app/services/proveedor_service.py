"""
app/services/proveedor_service.py
Business logic for suppliers and supplier-input relationships.
Author: charlykj
Issue: #38
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.proveedor_repo import ProveedorRepository, InsumoProveedorRepository


class ProveedorService:
    def __init__(self, db: AsyncSession):
        self.repo = ProveedorRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_proveedor: int):
        return await self.repo.get_by_id(id_proveedor)

    async def crear(self, data):
        return await self.repo.create(data)

    async def actualizar(self, id_proveedor: int, data):
        return await self.repo.update(id_proveedor, data)

    async def eliminar(self, id_proveedor: int):
        return await self.repo.delete(id_proveedor)


class InsumoProveedorService:
    def __init__(self, db: AsyncSession):
        self.repo = InsumoProveedorRepository(db)

    async def listar(self):
        return await self.repo.get_all()

    async def obtener(self, id_insumo_proveedor: int):
        return await self.repo.get_by_id(id_insumo_proveedor)

    async def crear(self, data):
        return await self.repo.create(data)

    async def eliminar(self, id_insumo_proveedor: int):
        return await self.repo.delete(id_insumo_proveedor)