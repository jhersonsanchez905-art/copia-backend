"""
receta_service.py
Async business logic for RecetaVersion, RecetaDetalleInsumo,
RecetaDetalleSubreceta, and RecetaPaso.

Rule: new recipe versions deactivate previous ones automatically.
The historical version remains immutable as the truth of what was consumed.
"""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.receta import (
    RecetaVersion,
    RecetaDetalleInsumo,
    RecetaDetalleSubreceta,
    RecetaPaso,
)
from app.repositories import receta_repo, producto_repo
from app.schemas.receta_schema import (
    RecetaVersionCreate,
    RecetaVersionUpdate,
    RecetaDetalleInsumoCreate,
    RecetaDetalleInsumoUpdate,
    RecetaDetalleSubrecetaCreate,
    RecetaDetalleSubrecetaUpdate,
    RecetaPasoCreate,
    RecetaPasoUpdate,
)


async def _calcular_costo_version(db: AsyncSession, version_id: int) -> Decimal:
    """Calculate and persist cost breakdown for all detail lines in a RecetaVersion.

    Writes costo_unitario, costo_total, pct_participacion on each detalle line
    and updates RecetaVersion.costo_total. Returns the computed total cost.
    """
    lineas: list[tuple] = []  # (detalle_obj, costo_line)

    # ── Detalles insumo ──────────────────────────────────────────────────────
    res = await db.execute(
        select(RecetaDetalleInsumo)
        .options(selectinload(RecetaDetalleInsumo.insumo))
        .where(RecetaDetalleInsumo.id_receta_version == version_id)
    )
    for d in res.scalars().all():
        insumo = d.insumo
        if insumo and insumo.precio is not None:
            if insumo.pct_rendimiento:
                costo_unit = insumo.precio / (insumo.pct_rendimiento / Decimal("100"))
            else:
                costo_unit = insumo.precio
        else:
            costo_unit = Decimal("0")
        costo_line = d.cantidad * costo_unit
        d.costo_unitario = costo_unit
        d.costo_total = costo_line
        lineas.append((d, costo_line))

    # ── Detalles subreceta ───────────────────────────────────────────────────
    res = await db.execute(
        select(RecetaDetalleSubreceta)
        .options(selectinload(RecetaDetalleSubreceta.subreceta))
        .where(RecetaDetalleSubreceta.id_receta_version == version_id)
    )
    for d in res.scalars().all():
        sub = d.subreceta
        costo_sub = Decimal(str(sub.costo_total or 0)) if sub else Decimal("0")
        porciones = Decimal(str(sub.porciones or 1)) if sub else Decimal("1")
        costo_unit = costo_sub / porciones
        costo_line = d.cantidad * costo_unit
        d.costo_unitario = costo_unit
        d.costo_total = costo_line
        lineas.append((d, costo_line))

    sum_total = sum(c for _, c in lineas) if lineas else Decimal("0")
    divisor = sum_total if sum_total else Decimal("1")

    for d, costo_line in lineas:
        d.pct_participacion = (costo_line / divisor * 100).quantize(Decimal("0.01"))

    version = await db.get(RecetaVersion, version_id)
    if version:
        version.costo_total = sum_total

    await db.flush()
    return sum_total


# ── RecetaVersion ─────────────────────────────────────────────────────────────

async def listar_todas_las_versiones(
    db: AsyncSession,
    *,
    solo_vigente: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[RecetaVersion]:
    return await receta_repo.get_all_versions(db, solo_vigente=solo_vigente, skip=skip, limit=limit)


async def listar_versiones(
    db: AsyncSession, producto_id: int, *, solo_vigente: bool = False
) -> list[RecetaVersion]:
    producto = await producto_repo.get_by_id(db, producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Producto {producto_id} no encontrado")
    return await receta_repo.get_versions_by_producto(db, producto_id, solo_vigente=solo_vigente)


async def obtener_version(db: AsyncSession, version_id: int) -> RecetaVersion:
    version = await receta_repo.get_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaVersion {version_id} no encontrada")
    return version


async def crear_version(db: AsyncSession, payload: RecetaVersionCreate) -> RecetaVersion:
    producto = await producto_repo.get_by_id(db, payload.id_producto)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Producto {payload.id_producto} no encontrado")

    await receta_repo.deactivate_current_versions(db, payload.id_producto)
    next_version = await receta_repo.get_next_version_number(db, payload.id_producto)

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

    for d in payload.detalles_insumo:
        detalle = RecetaDetalleInsumo(id_receta_version=version.id_receta_version, **d.model_dump())
        await receta_repo.create_detalle_insumo(db, detalle)

    for d in payload.detalles_subreceta:
        detalle = RecetaDetalleSubreceta(id_receta_version=version.id_receta_version, **d.model_dump())
        await receta_repo.create_detalle_subreceta(db, detalle)

    for p in payload.pasos:
        paso = RecetaPaso(id_receta_version=version.id_receta_version, **p.model_dump())
        await receta_repo.create_paso(db, paso)

    await db.flush()
    await _calcular_costo_version(db, version.id_receta_version)

    await db.commit()
    return await receta_repo.get_version_by_id(db, version.id_receta_version)


async def actualizar_version(
    db: AsyncSession, version_id: int, payload: RecetaVersionUpdate
) -> RecetaVersion:
    version = await obtener_version(db, version_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se enviaron campos para actualizar")
    await receta_repo.update_version(db, version, data)
    await db.commit()
    return await receta_repo.get_version_by_id(db, version.id_receta_version)


# ── RecetaDetalleInsumo ───────────────────────────────────────────────────────

async def agregar_detalle_insumo(
    db: AsyncSession, version_id: int, payload: RecetaDetalleInsumoCreate
) -> RecetaDetalleInsumo:
    await obtener_version(db, version_id)
    detalle = RecetaDetalleInsumo(id_receta_version=version_id, **payload.model_dump())
    detalle = await receta_repo.create_detalle_insumo(db, detalle)
    await _calcular_costo_version(db, version_id)
    await db.commit()
    return detalle


async def actualizar_detalle_insumo(
    db: AsyncSession, detalle_id: int, payload: RecetaDetalleInsumoUpdate
) -> RecetaDetalleInsumo:
    detalle = await receta_repo.get_detalle_insumo_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaDetalleInsumo {detalle_id} no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se enviaron campos para actualizar")
    detalle = await receta_repo.update_detalle_insumo(db, detalle, data)
    await _calcular_costo_version(db, detalle.id_receta_version)
    await db.commit()
    return detalle


async def eliminar_detalle_insumo(db: AsyncSession, detalle_id: int) -> None:
    detalle = await receta_repo.get_detalle_insumo_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaDetalleInsumo {detalle_id} no encontrado")
    await receta_repo.delete_detalle_insumo(db, detalle)
    await db.commit()


# ── RecetaDetalleSubreceta ────────────────────────────────────────────────────

async def agregar_detalle_subreceta(
    db: AsyncSession, version_id: int, payload: RecetaDetalleSubrecetaCreate
) -> RecetaDetalleSubreceta:
    await obtener_version(db, version_id)
    detalle = RecetaDetalleSubreceta(id_receta_version=version_id, **payload.model_dump())
    detalle = await receta_repo.create_detalle_subreceta(db, detalle)
    await _calcular_costo_version(db, version_id)
    await db.commit()
    return detalle


async def actualizar_detalle_subreceta(
    db: AsyncSession, detalle_id: int, payload: RecetaDetalleSubrecetaUpdate
) -> RecetaDetalleSubreceta:
    detalle = await receta_repo.get_detalle_subreceta_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaDetalleSubreceta {detalle_id} no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se enviaron campos para actualizar")
    detalle = await receta_repo.update_detalle_subreceta(db, detalle, data)
    await _calcular_costo_version(db, detalle.id_receta_version)
    await db.commit()
    return detalle


async def eliminar_detalle_subreceta(db: AsyncSession, detalle_id: int) -> None:
    detalle = await receta_repo.get_detalle_subreceta_by_id(db, detalle_id)
    if detalle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaDetalleSubreceta {detalle_id} no encontrado")
    await receta_repo.delete_detalle_subreceta(db, detalle)
    await db.commit()


# ── RecetaPaso ────────────────────────────────────────────────────────────────

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
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaPaso {paso_id} no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se enviaron campos para actualizar")
    paso = await receta_repo.update_paso(db, paso, data)
    await db.commit()
    return paso


async def eliminar_paso(db: AsyncSession, paso_id: int) -> None:
    paso = await receta_repo.get_paso_by_id(db, paso_id)
    if paso is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"RecetaPaso {paso_id} no encontrado")
    await receta_repo.delete_paso(db, paso)
    await db.commit()
