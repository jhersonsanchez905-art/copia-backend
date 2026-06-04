"""
app/repositories/catalogo_repo.py
Database repository for base catalog operations in the POS system.
Author: charlykj
Issue: #38
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.catalogo import Rol, Usuario, Cliente, Marca, UnidadMedida, Clasificacion, Categoria, MetodoPago


class RolRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Rol))
        return result.scalars().all()

    async def get_by_id(self, id_rol: int):
        result = await self.db.execute(select(Rol).where(Rol.id_rol == id_rol))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Rol(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_rol: int):
        obj = await self.get_by_id(id_rol)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Usuario))
        return result.scalars().all()

    async def get_by_id(self, id_usuario: int):
        result = await self.db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Usuario(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, id_usuario: int, data):
        obj = await self.get_by_id(id_usuario)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_usuario: int):
        obj = await self.get_by_id(id_usuario)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class ClienteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Cliente))
        return result.scalars().all()

    async def get_by_id(self, id_cliente: int):
        result = await self.db.execute(select(Cliente).where(Cliente.id_cliente == id_cliente))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Cliente(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, id_cliente: int, data):
        obj = await self.get_by_id(id_cliente)
        if not obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_cliente: int):
        obj = await self.get_by_id(id_cliente)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class MarcaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Marca))
        return result.scalars().all()

    async def get_by_id(self, id_marca: int):
        result = await self.db.execute(select(Marca).where(Marca.id_marca == id_marca))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Marca(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_marca: int):
        obj = await self.get_by_id(id_marca)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class UnidadMedidaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(UnidadMedida))
        return result.scalars().all()

    async def get_by_id(self, id_unidad: int):
        result = await self.db.execute(select(UnidadMedida).where(UnidadMedida.id_unidad == id_unidad))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = UnidadMedida(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_unidad: int):
        obj = await self.get_by_id(id_unidad)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class ClasificacionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Clasificacion))
        return result.scalars().all()

    async def get_by_id(self, id_clasificacion: int):
        result = await self.db.execute(select(Clasificacion).where(Clasificacion.id_clasificacion == id_clasificacion))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Clasificacion(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_clasificacion: int):
        obj = await self.get_by_id(id_clasificacion)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class CategoriaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(Categoria))
        return result.scalars().all()

    async def get_by_id(self, id_categoria: int):
        result = await self.db.execute(select(Categoria).where(Categoria.id_categoria == id_categoria))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = Categoria(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_categoria: int):
        obj = await self.get_by_id(id_categoria)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


class MetodoPagoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self):
        result = await self.db.execute(select(MetodoPago))
        return result.scalars().all()

    async def get_by_id(self, id_metodo_pago: int):
        result = await self.db.execute(select(MetodoPago).where(MetodoPago.id_metodo_pago == id_metodo_pago))
        return result.scalar_one_or_none()

    async def create(self, data):
        obj = MetodoPago(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id_metodo_pago: int):
        obj = await self.get_by_id(id_metodo_pago)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True