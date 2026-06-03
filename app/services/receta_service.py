"""
receta_service.py
Lógica de negocio para RecetaVersion, RecetaDetalle y RecetaPaso.

Regla de negocio clave (Plan de Desarrollo §2.1):
  «Recetas versionadas: los cambios en recetas aplican a ventas futuras.
   El histórico permanece inmutable como verdad de lo que realmente se consumió.»

Al crear una nueva versión se desactivan las anteriores automáticamente.
Autor SebastianValero12
Issue: #40
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receta import RecetaVersion, RecetaDetalle, RecetaPaso
from app.repositories import receta_repo, producto_repo
from app.schemas.receta_schema import (
    RecetaVersionCreate,
    RecetaVersionUpdate,
    RecetaDetalleCreate,
    RecetaDetalleUpdate,
    RecetaPasoCreate,
    RecetaPasoUpdate,
)


# ── RecetaVersion ───────────────────────────────────────────

async def listar_versiones(
    db: AsyncSession, producto_id: int, *, solo_vigente: bool = False
) -> list[RecetaVersion]:
    producto = await producto_repo.get_by_id(db, producto_id)
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado",
        )
    return await receta_repo.get_versions_by_producto(
        db, producto_id, solo_vigente=solo_vigente
    )


async def obtener_version(
    db: AsyncSession, version_id: int
) -> RecetaVersion:
    version = await receta_repo.get_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecetaVersion {version_id} no encontrada",
        )
    return version


async def crear_version(
    db: AsyncSession, payload: RecetaVersionCreate
) -> RecetaVersion:
    """
    Crea una nueva versión de receta para un producto.
    - Calcula el próximo número de versión automáticamente.
    - Desactiva las versiones vigentes anteriores.
    - Crea detalles y pasos en cascada dentro de la misma transacción.
    """
    # Validar que el producto existe
    producto = await producto_repo.get_by_id(db, payload.id_producto)
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {payload.id_producto} no encontrado",
        )

    # Desactivar versiones anteriores y calcular nuevo número
    await receta_repo.deactivate_current_versions(db, payload.id_producto)
    next_version = await receta_repo.get_next_version_number(
        db, payload.id_producto
    )

    # Crear la versión
    version = RecetaVersion(
        id_producto=payload.id_producto,
        version=next_version,
        vigente=True,
        costo_total=payload.costo_total,
        tiempo_preparacion_min=payload.tiempo_preparacion_min,
        instrucciones_generales=payload.instrucciones_generales,
        observaciones=payload.observaciones,
    )
    version = await receta_repo.create_version(db, version)

    # Crear detalles
    for d in payload.detalles:
        detalle = RecetaDetalle(
            id_receta_version=version.id_receta_version,
            **d.model_dump(),
        )
        await receta_repo.create_detalle(db, detalle)

    # Crear pasos
    for p in payload.pasos:
        paso = RecetaPaso(
            id_receta_version=version.id_receta_version,
            **p.model_dump(),
        )
        await receta_repo.create_paso(db, paso)

    await db.commit()

    # Recargar con relaciones
    return await receta_repo.get_version_by_id(db, version.id_receta_version)


async def actualizar_version(
    db: AsyncSession, version_id: int, payload: RecetaVersionUpdate
) -> RecetaVersion:
    """Actualiza solo los metadatos de una versión (no detalles ni pasos)."""
    version = await obtener_version(db, version_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron campos para actualizar",
        )
    version = await receta_repo.update_version(db, version, data)
    await db.commit()
    return await receta_repo.get_version_by_id(db, version.id_receta_version)


# ── RecetaDetalle ───────────────────────────────────────────

async def agregar_detalle(
    db: AsyncSession, version_id: int, payload: RecetaDetalleCreate
) -> RecetaDetalle:
    await obtener_version(db, version_id)
    detalle = RecetaDetalle(
        id_receta_version=version_id, **payload.model_dump()
    )
    detalle = await receta_repo.create_detalle(db, detalle)
    await db.commit()
    return detalle


async def actualizar_detalle(
    db: AsyncSession, detalle_id: int, payload: RecetaDetalleUpdate
) -> RecetaDetalle:
    detalle = await receta_repo.get_detalle_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecetaDetalle {detalle_id} no encontrado",
        )
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron campos para actualizar",
        )
    detalle = await receta_repo.update_detalle(db, detalle, data)
    await db.commit()
    return detalle


async def eliminar_detalle(db: AsyncSession, detalle_id: int) -> None:
    detalle = await receta_repo.get_detalle_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecetaDetalle {detalle_id} no encontrado",
        )
    await receta_repo.delete_detalle(db, detalle)
    await db.commit()


# ── RecetaPaso ──────────────────────────────────────────────

async def agregar_paso(
    db: AsyncSession, version_id: int, payload: RecetaPasoCreate
) -> RecetaPaso:
    await obtener_version(db, version_id)
    paso = RecetaPaso(id_receta_version=version_id, **payload.model_dump())
    paso = await receta_repo.create_paso(db, paso)
    await db.commit()
    return paso


async def actualizar_paso(
    db: AsyncSession, paso_id: int, payload: RecetaPasoUpdate
) -> RecetaPaso:
    paso = await receta_repo.get_paso_by_id(db, paso_id)
    if paso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecetaPaso {paso_id} no encontrado",
        )
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron campos para actualizar",
        )
    paso = await receta_repo.update_paso(db, paso, data)
    await db.commit()
    return paso


async def eliminar_paso(db: AsyncSession, paso_id: int) -> None:
    paso = await receta_repo.get_paso_by_id(db, paso_id)
    if paso is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecetaPaso {paso_id} no encontrado",
        )
    await receta_repo.delete_paso(db, paso)
    await db.commit()