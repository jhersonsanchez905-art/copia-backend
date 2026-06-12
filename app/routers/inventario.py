"""
inventario.py (router)
Endpoints for inventory alerts and stock movements.
AjusteInventario endpoints are in ajuste_inventario.py router.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.exceptions import MajesaError
from app.models.catalogo import Usuario
from app.repositories import insumo_repo
from app.schemas.inventario_schema import AlertaResponse, MovimientoResponse
from app.services import inventario_service

router = APIRouter()


@router.get(
    "/alertas",
    response_model=list[AlertaResponse],
    summary="Listar todas las alertas de stock activas",
)
async def get_alertas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await inventario_service.get_alertas_activas(db)


@router.get(
    "/movimientos/{id_insumo}",
    response_model=list[MovimientoResponse],
    summary="Listar movimientos de inventario de un insumo",
)
async def get_movimientos(
    id_insumo: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not await insumo_repo.get_insumo_by_id(db, id_insumo):
        raise MajesaError(f"Insumo {id_insumo} no encontrado", 404)
    return await inventario_service.get_movimientos_by_insumo(db, id_insumo)
