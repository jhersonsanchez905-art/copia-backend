"""
ajuste_inventario.py (router)
Endpoints for manual inventory adjustments with approval flow.
Only Administrador can approve or reject adjustments.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_rol
from app.models.catalogo import Usuario
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
    current_user: Usuario = Depends(get_current_user),
):
    return await ajuste_inventario_service.get_ajustes(
        db,
        estado=estado.value if estado else None,
        id_insumo=id_insumo,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_ajuste}", response_model=AjusteInventarioResponse)
async def obtener_ajuste(
    id_ajuste: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await ajuste_inventario_service.get_ajuste_by_id(db, id_ajuste)


@router.post(
    "",
    response_model=AjusteInventarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar ajuste manual de inventario (queda en estado pendiente)",
)
async def solicitar_ajuste(
    data: AjusteInventarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await ajuste_inventario_service.solicitar_ajuste(db, data, current_user.id_usuario)


@router.patch(
    "/{id_ajuste}/resolver",
    response_model=AjusteInventarioResponse,
    summary="Aprobar o rechazar ajuste (solo Administrador)",
)
async def resolver_ajuste(
    id_ajuste: int,
    data: AjusteInventarioAprobacion,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await ajuste_inventario_service.resolver_ajuste(
        db, id_ajuste, data, current_user.id_usuario, es_administrador=True
    )
