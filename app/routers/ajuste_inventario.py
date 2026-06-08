"""
ajuste_inventario.py
Endpoints para ajustes manuales de inventario con flujo de aprobación.
Autor: Ivan Ospino
Issue: #21
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ajuste_inventario_schema import (
    AjusteInventarioAprobar,
    AjusteInventarioRechazar,
    AjusteInventarioCreate,
    AjusteInventarioResponse,
    EstadoAjusteEnum,
)
from app.services import ajuste_inventario_service

router = APIRouter(prefix="/ajustes-inventario", tags=["Ajustes de Inventario"])


@router.get("", response_model=list[AjusteInventarioResponse])
async def listar_ajustes(
    estado: EstadoAjusteEnum | None = Query(None),
    id_insumo: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await ajuste_inventario_service.get_ajustes(
        db,
        estado=estado.value if estado else None,
        id_insumo=id_insumo,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_ajuste}", response_model=AjusteInventarioResponse)
async def obtener_ajuste(id_ajuste: int, db: AsyncSession = Depends(get_db)):
    return await ajuste_inventario_service.get_ajuste_by_id(db, id_ajuste)


@router.post("", response_model=AjusteInventarioResponse, status_code=status.HTTP_201_CREATED)
async def solicitar_ajuste(
    data: AjusteInventarioCreate, db: AsyncSession = Depends(get_db)
):
    # TODO: extraer id_usuario del token Clerk
    id_usuario = 1
    return await ajuste_inventario_service.solicitar_ajuste(db, data, id_usuario)


@router.patch("/{id_ajuste}/aprobar", response_model=AjusteInventarioResponse)
async def aprobar_ajuste(
    id_ajuste: int,
    data: AjusteInventarioAprobar,
    db: AsyncSession = Depends(get_db),
):
    # TODO: extraer id_usuario y validar rol Administrador desde token Clerk
    id_aprobador = 1
    es_administrador = True
    return await ajuste_inventario_service.aprobar_ajuste(
        db, id_ajuste, data, id_aprobador, es_administrador
    )


@router.patch("/{id_ajuste}/rechazar", response_model=AjusteInventarioResponse)
async def rechazar_ajuste(
    id_ajuste: int,
    data: AjusteInventarioRechazar,
    db: AsyncSession = Depends(get_db),
):
    # TODO: extraer id_usuario y validar rol Administrador desde token Clerk
    id_aprobador = 1
    es_administrador = True
    return await ajuste_inventario_service.rechazar_ajuste(
        db, id_ajuste, data, id_aprobador, es_administrador
    )