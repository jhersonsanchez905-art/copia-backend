"""
app/repositories/proveedor_repo.py
Database repository for supplier and supplier-input operations.
Author: charlykj
Issue: #38
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.proveedor import Proveedor, InsumoProveedor


class ProveedorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Proveedor))
        return result.scalars().all()

    async def get_by_id(self, id_proveedor: int):
        result = await self.db.execute(select(Proveedor).where(Proveedor.id_proveedor == id_proveedor))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Proveedor(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, id_proveedor: int, data):
        obj = await self.get_by_id(id_proveedor)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_proveedor: int):
        obj = await self.get_by_id(id_proveedor)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class InsumoProveedorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(InsumoProveedor))
        return result.scalars().all()

    async def get_by_id(self, id_insumo_proveedor: int):
        result = await self.db.execute(select(InsumoProveedor).where(InsumoProveedor.id_insumo_proveedor == id_insumo_proveedor))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = InsumoProveedor(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_insumo_proveedor: int):
        obj = await self.get_by_id(id_insumo_proveedor)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True