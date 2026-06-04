"""
producto.py (router)
Endpoints CRUD para Producto.
Autor SebastianValero12
Issue: #40
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.producto_schema import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse,
)
from app.services import producto_service

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get(
    "",
    response_model=dict,
    summary="Listar productos",
    description="Retorna productos paginados. Filtrar por categoría o estado activo.",
)
async def listar_productos(
    solo_activos: bool = Query(True),
    id_categoria: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await producto_service.listar_productos(
        db,
        solo_activos=solo_activos,
        id_categoria=id_categoria,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener producto por ID",
)
async def obtener_producto(
    producto_id: int, db: AsyncSession = Depends(get_db)
):
    return await producto_service.obtener_producto(db, producto_id)


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto",
)
async def crear_producto(
    payload: ProductoCreate, db: AsyncSession = Depends(get_db)
):
    return await producto_service.crear_producto(db, payload)


@router.patch(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Actualizar producto (parcial)",
)
async def actualizar_producto(
    producto_id: int,
    payload: ProductoUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await producto_service.actualizar_producto(db, producto_id, payload)


@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar producto",
)
async def eliminar_producto(
    producto_id: int, db: AsyncSession = Depends(get_db)
):
    await producto_service.eliminar_producto(db, producto_id)