"""
servicio_adicional.py (router)
CRUD endpoints for ServicioAdicional.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_rol
from app.models.catalogo import Usuario
from app.schemas.servicio_adicional_schema import (
    ServicioAdicionalCreate,
    ServicioAdicionalUpdate,
    ServicioAdicionalResponse,
)
from app.services import servicio_adicional_service

router = APIRouter(prefix="/servicios-adicionales", tags=["Servicios Adicionales"])


@router.get("", response_model=list[ServicioAdicionalResponse])
async def listar_servicios(
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await servicio_adicional_service.get_servicios(db, solo_activos=solo_activos)


@router.get("/{id_servicio}", response_model=ServicioAdicionalResponse)
async def obtener_servicio(
    id_servicio: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await servicio_adicional_service.get_servicio(db, id_servicio)


@router.post(
    "",
    response_model=ServicioAdicionalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_servicio(
    data: ServicioAdicionalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await servicio_adicional_service.create_servicio(db, data)


@router.patch("/{id_servicio}", response_model=ServicioAdicionalResponse)
async def actualizar_servicio(
    id_servicio: int,
    data: ServicioAdicionalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await servicio_adicional_service.update_servicio(db, id_servicio, data)
