"""
servicio_adicional_service.py
Async business logic for ServicioAdicional.
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.servicio_adicional import ServicioAdicional
from app.repositories import servicio_adicional_repo
from app.schemas.servicio_adicional_schema import ServicioAdicionalCreate, ServicioAdicionalUpdate


async def get_servicio(db: AsyncSession, id_servicio: int) -> ServicioAdicional:
    servicio = await servicio_adicional_repo.get_servicio_by_id(db, id_servicio)
    if not servicio:
        raise MajesaError(f"ServicioAdicional {id_servicio} no encontrado", 404)
    return servicio


async def get_servicios(
    db: AsyncSession, solo_activos: bool = True
) -> list[ServicioAdicional]:
    return await servicio_adicional_repo.get_servicios(db, solo_activos=solo_activos)


async def create_servicio(
    db: AsyncSession, data: ServicioAdicionalCreate
) -> ServicioAdicional:
    servicio = ServicioAdicional(**data.model_dump())
    servicio = await servicio_adicional_repo.create_servicio(db, servicio)
    await db.commit()
    return servicio


async def update_servicio(
    db: AsyncSession, id_servicio: int, data: ServicioAdicionalUpdate
) -> ServicioAdicional:
    servicio = await get_servicio(db, id_servicio)
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No hay campos para actualizar")
    servicio = await servicio_adicional_repo.update_servicio(db, servicio, fields)
    await db.commit()
    return servicio
<<<<<<< HEAD
=======
async def cambiar_estado_servicio(
    db: AsyncSession, id_servicio: int, activo: bool
) -> ServicioAdicional:
    """Activate or deactivate a service."""
    servicio = await get_servicio(db, id_servicio)
    servicio = await servicio_adicional_repo.update_servicio(db, servicio, {"activo": activo})
    await db.commit()
    return servicio
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
