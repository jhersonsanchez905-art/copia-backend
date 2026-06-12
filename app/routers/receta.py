"""
receta.py (router)
CRUD endpoints for RecetaVersion, RecetaDetalleInsumo,
RecetaDetalleSubreceta, and RecetaPaso.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.receta_schema import (
    RecetaVersionCreate,
    RecetaVersionUpdate,
    RecetaVersionResponse,
    RecetaDetalleInsumoCreate,
    RecetaDetalleInsumoUpdate,
    RecetaDetalleInsumoResponse,
    RecetaDetalleSubrecetaCreate,
    RecetaDetalleSubrecetaUpdate,
    RecetaDetalleSubrecetaResponse,
    RecetaPasoCreate,
    RecetaPasoUpdate,
    RecetaPasoResponse,
)
from app.services import receta_service

router = APIRouter(prefix="/recetas", tags=["Recetas"])


# ── RecetaVersion ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[RecetaVersionResponse], summary="Listar todas las recetas")
async def listar_todas_las_recetas(
    solo_vigente: bool = Query(False, description="Solo versiones vigentes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await receta_service.listar_todas_las_versiones(db, solo_vigente=solo_vigente, skip=skip, limit=limit)


@router.get(
    "/producto/{producto_id}",
    response_model=list[RecetaVersionResponse],
    summary="Listar versiones de receta de un producto",
)
async def listar_versiones(
    producto_id: int,
    solo_vigente: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await receta_service.listar_versiones(db, producto_id, solo_vigente=solo_vigente)


@router.get(
    "/producto/{producto_id}/historial",
    response_model=list[RecetaVersionResponse],
    summary="Historial completo de versiones de receta de un producto",
)
async def historial_recetas(
    producto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await receta_service.listar_versiones(db, producto_id, solo_vigente=False)


@router.get(
    "/{version_id}",
    response_model=RecetaVersionResponse,
    summary="Obtener versión de receta por ID",
)
async def obtener_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await receta_service.obtener_version(db, version_id)


@router.post(
    "",
    response_model=RecetaVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva versión de receta (desactiva versiones anteriores)",
)
async def crear_version(
    payload: RecetaVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
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
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.actualizar_version(db, version_id, payload)


# ── RecetaDetalleInsumo ───────────────────────────────────────────────────────

@router.post(
    "/{version_id}/detalles/insumo",
    response_model=RecetaDetalleInsumoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar detalle de insumo a una versión de receta",
)
async def agregar_detalle_insumo(
    version_id: int,
    payload: RecetaDetalleInsumoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.agregar_detalle_insumo(db, version_id, payload)


@router.patch(
    "/detalles/insumo/{detalle_id}",
    response_model=RecetaDetalleInsumoResponse,
    summary="Actualizar detalle de insumo",
)
async def actualizar_detalle_insumo(
    detalle_id: int,
    payload: RecetaDetalleInsumoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.actualizar_detalle_insumo(db, detalle_id, payload)


@router.delete(
    "/detalles/insumo/{detalle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar detalle de insumo",
)
async def eliminar_detalle_insumo(
    detalle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    await receta_service.eliminar_detalle_insumo(db, detalle_id)


# ── RecetaDetalleSubreceta ────────────────────────────────────────────────────

@router.post(
    "/{version_id}/detalles/subreceta",
    response_model=RecetaDetalleSubrecetaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar detalle de subreceta a una versión de receta",
)
async def agregar_detalle_subreceta(
    version_id: int,
    payload: RecetaDetalleSubrecetaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.agregar_detalle_subreceta(db, version_id, payload)


@router.patch(
    "/detalles/subreceta/{detalle_id}",
    response_model=RecetaDetalleSubrecetaResponse,
    summary="Actualizar detalle de subreceta",
)
async def actualizar_detalle_subreceta(
    detalle_id: int,
    payload: RecetaDetalleSubrecetaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.actualizar_detalle_subreceta(db, detalle_id, payload)


@router.delete(
    "/detalles/subreceta/{detalle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar detalle de subreceta",
)
async def eliminar_detalle_subreceta(
    detalle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    await receta_service.eliminar_detalle_subreceta(db, detalle_id)


# ── RecetaPaso ────────────────────────────────────────────────────────────────

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
    current_user: Usuario = Depends(require_rol("administrador")),
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
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await receta_service.actualizar_paso(db, paso_id, payload)


@router.delete(
    "/pasos/{paso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar paso de receta",
)
async def eliminar_paso(
    paso_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    await receta_service.eliminar_paso(db, paso_id)
