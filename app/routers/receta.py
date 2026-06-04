"""
receta.py (router)
Endpoints CRUD para RecetaVersion, RecetaDetalle y RecetaPaso.
Autor SebastianValero12
Issue: #40
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.receta_schema import (
    RecetaVersionCreate,
    RecetaVersionUpdate,
    RecetaVersionResponse,
    RecetaDetalleCreate,
    RecetaDetalleUpdate,
    RecetaDetalleResponse,
    RecetaPasoCreate,
    RecetaPasoUpdate,
    RecetaPasoResponse,
)
from app.services import receta_service

router = APIRouter(prefix="/recetas", tags=["Recetas"])


# ── RecetaVersion ───────────────────────────────────────────

@router.get(
    "/producto/{producto_id}",
    response_model=list[RecetaVersionResponse],
    summary="Listar versiones de receta de un producto",
)
async def listar_versiones(
    producto_id: int,
    solo_vigente: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.listar_versiones(
        db, producto_id, solo_vigente=solo_vigente
    )


@router.get(
    "/{version_id}",
    response_model=RecetaVersionResponse,
    summary="Obtener versión de receta por ID (incluye detalles y pasos)",
)
async def obtener_version(
    version_id: int, db: AsyncSession = Depends(get_db)
):
    return await receta_service.obtener_version(db, version_id)


@router.post(
    "",
    response_model=RecetaVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva versión de receta",
    description=(
        "Crea una nueva versión para el producto indicado. "
        "Desactiva automáticamente las versiones anteriores. "
        "Acepta detalles (ingredientes) y pasos en cascada."
    ),
)
async def crear_version(
    payload: RecetaVersionCreate, db: AsyncSession = Depends(get_db)
):
    return await receta_service.crear_version(db, payload)


@router.patch(
    "/{version_id}",
    response_model=RecetaVersionResponse,
    summary="Actualizar metadatos de una versión",
)
async def actualizar_version(
    version_id: int,
    payload: RecetaVersionUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.actualizar_version(db, version_id, payload)


# ── RecetaDetalle ───────────────────────────────────────────

@router.post(
    "/{version_id}/detalles",
    response_model=RecetaDetalleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar ingrediente a una versión de receta",
)
async def agregar_detalle(
    version_id: int,
    payload: RecetaDetalleCreate,
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.agregar_detalle(db, version_id, payload)


@router.patch(
    "/detalles/{detalle_id}",
    response_model=RecetaDetalleResponse,
    summary="Actualizar ingrediente de receta",
)
async def actualizar_detalle(
    detalle_id: int,
    payload: RecetaDetalleUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.actualizar_detalle(db, detalle_id, payload)


@router.delete(
    "/detalles/{detalle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar ingrediente de receta",
)
async def eliminar_detalle(
    detalle_id: int, db: AsyncSession = Depends(get_db)
):
    await receta_service.eliminar_detalle(db, detalle_id)


# ── RecetaPaso ──────────────────────────────────────────────

@router.post(
    "/{version_id}/pasos",
    response_model=RecetaPasoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar paso a una versión de receta",
)
async def agregar_paso(
    version_id: int,
    payload: RecetaPasoCreate,
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.agregar_paso(db, version_id, payload)


@router.patch(
    "/pasos/{paso_id}",
    response_model=RecetaPasoResponse,
    summary="Actualizar paso de receta",
)
async def actualizar_paso(
    paso_id: int,
    payload: RecetaPasoUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await receta_service.actualizar_paso(db, paso_id, payload)


@router.delete(
    "/pasos/{paso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar paso de receta",
)
async def eliminar_paso(
    paso_id: int, db: AsyncSession = Depends(get_db)
):
    await receta_service.eliminar_paso(db, paso_id)