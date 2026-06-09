"""
ajuste_inventario.py (router)
Endpoints for manual inventory adjustments with approval flow.
Only Administrador can approve or reject adjustments.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ajuste_inventario_schema import (
    AjusteInventarioAprobacion,
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


@router.post(
    "",
    response_model=AjusteInventarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar ajuste manual de inventario (queda en estado pendiente)",
)
async def solicitar_ajuste(
    data: AjusteInventarioCreate, db: AsyncSession = Depends(get_db)
):
    # TODO: extract id_usuario from Clerk token
    id_usuario = 1
    return await ajuste_inventario_service.solicitar_ajuste(db, data, id_usuario)


@router.patch(
    "/{id_ajuste}/resolver",
    response_model=AjusteInventarioResponse,
    summary="Aprobar o rechazar ajuste (solo Administrador)",
)
async def resolver_ajuste(
    id_ajuste: int,
    data: AjusteInventarioAprobacion,
    db: AsyncSession = Depends(get_db),
):
    # TODO: extract id_usuario and validate Administrador role from Clerk token
    id_aprobador = 1
    es_administrador = True  # placeholder until Clerk auth is wired
    return await ajuste_inventario_service.resolver_ajuste(
        db, id_ajuste, data, id_aprobador, es_administrador
    )
