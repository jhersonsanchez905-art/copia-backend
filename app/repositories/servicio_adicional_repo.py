"""
servicio_adicional_repo.py
Async repository for ServicioAdicional.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.servicio_adicional import ServicioAdicional


async def get_servicio_by_id(
    db: AsyncSession, id_servicio: int
) -> ServicioAdicional | None:
    return await db.get(ServicioAdicional, id_servicio)


async def get_servicios(
    db: AsyncSession, solo_activos: bool = True
) -> list[ServicioAdicional]:
    query = select(ServicioAdicional)
    if solo_activos:
        query = query.where(ServicioAdicional.activo.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_servicio(
    db: AsyncSession, servicio: ServicioAdicional
) -> ServicioAdicional:
    db.add(servicio)
    await db.flush()
    await db.refresh(servicio)
    return servicio


async def update_servicio(
    db: AsyncSession, servicio: ServicioAdicional, data: dict
) -> ServicioAdicional:
    for key, value in data.items():
        setattr(servicio, key, value)
    await db.flush()
    await db.refresh(servicio)
    return servicio
