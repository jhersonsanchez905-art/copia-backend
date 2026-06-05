"""
ajuste_inventario_repo.py
Async repository for AjusteInventario (manual stock adjustments with approval flow).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ajuste_inventario import AjusteInventario


async def create_ajuste(db: AsyncSession, ajuste: AjusteInventario) -> AjusteInventario:
    db.add(ajuste)
    await db.flush()
    await db.refresh(ajuste)
    return ajuste


async def get_ajuste_by_id(
    db: AsyncSession, id_ajuste: int
) -> AjusteInventario | None:
    return await db.get(AjusteInventario, id_ajuste)


async def get_ajustes(
    db: AsyncSession,
    estado: str | None = None,
    id_insumo: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AjusteInventario]:
    query = select(AjusteInventario)
    if estado:
        query = query.where(AjusteInventario.estado == estado)
    if id_insumo:
        query = query.where(AjusteInventario.id_insumo == id_insumo)
    query = query.order_by(AjusteInventario.fecha_solicitud.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_ajuste(
    db: AsyncSession, ajuste: AjusteInventario, data: dict
) -> AjusteInventario:
    for key, value in data.items():
        setattr(ajuste, key, value)
    await db.flush()
    await db.refresh(ajuste)
    return ajuste
