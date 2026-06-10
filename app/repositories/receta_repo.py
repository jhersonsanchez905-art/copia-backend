"""
receta_repo.py
Async repository for RecetaVersion, RecetaDetalleInsumo,
RecetaDetalleSubreceta, and RecetaPaso.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.receta import (
    RecetaVersion,
    RecetaDetalleInsumo,
    RecetaDetalleSubreceta,
    RecetaPaso,
)


# ── RecetaVersion ─────────────────────────────────────────────────────────────

async def get_version_by_id(
    db: AsyncSession, version_id: int
) -> RecetaVersion | None:
    result = await db.execute(
        select(RecetaVersion)
        .options(
            selectinload(RecetaVersion.producto),
            selectinload(RecetaVersion.detalles_insumo),
            selectinload(RecetaVersion.detalles_subreceta),
            selectinload(RecetaVersion.pasos),
        )
        .where(RecetaVersion.id_receta_version == version_id)
    )
    return result.scalar_one_or_none()


async def get_vigente_by_producto(
    db: AsyncSession, producto_id: int
) -> RecetaVersion | None:
    result = await db.execute(
        select(RecetaVersion)
        .options(
            selectinload(RecetaVersion.detalles_insumo),
            selectinload(RecetaVersion.detalles_subreceta),
        )
        .where(
            RecetaVersion.id_producto == producto_id,
            RecetaVersion.vigente.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def get_versions_by_producto(
    db: AsyncSession,
    producto_id: int,
    *,
    solo_vigente: bool = False,
) -> list[RecetaVersion]:
    query = (
        select(RecetaVersion)
        .options(
            selectinload(RecetaVersion.producto),
            selectinload(RecetaVersion.detalles_insumo),
            selectinload(RecetaVersion.detalles_subreceta),
            selectinload(RecetaVersion.pasos),
        )
        .where(RecetaVersion.id_producto == producto_id)
    )
    if solo_vigente:
        query = query.where(RecetaVersion.vigente.is_(True))
    query = query.order_by(RecetaVersion.version.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_all_versions(
    db: AsyncSession,
    *,
    solo_vigente: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[RecetaVersion]:
    query = (
        select(RecetaVersion)
        .options(
            selectinload(RecetaVersion.producto),
            selectinload(RecetaVersion.detalles_insumo),
            selectinload(RecetaVersion.detalles_subreceta),
            selectinload(RecetaVersion.pasos),
        )
        .order_by(RecetaVersion.id_producto.asc(), RecetaVersion.version.desc())
    )
    if solo_vigente:
        query = query.where(RecetaVersion.vigente.is_(True))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_next_version_number(db: AsyncSession, producto_id: int) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(RecetaVersion.version), 0)).where(
            RecetaVersion.id_producto == producto_id
        )
    )
    return result.scalar_one() + 1


async def deactivate_current_versions(db: AsyncSession, producto_id: int) -> None:
    result = await db.execute(
        select(RecetaVersion)
        .where(RecetaVersion.id_producto == producto_id)
        .where(RecetaVersion.vigente.is_(True))
    )
    for version in result.scalars().all():
        version.vigente = False
    await db.flush()


async def create_version(db: AsyncSession, version: RecetaVersion) -> RecetaVersion:
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


async def update_version(
    db: AsyncSession, version: RecetaVersion, data: dict
) -> RecetaVersion:
    for key, value in data.items():
        setattr(version, key, value)
    await db.flush()
    await db.refresh(version)
    return version


# ── RecetaDetalleInsumo ───────────────────────────────────────────────────────

async def get_detalle_insumo_by_id(
    db: AsyncSession, detalle_id: int
) -> RecetaDetalleInsumo | None:
    return await db.get(RecetaDetalleInsumo, detalle_id)


async def create_detalle_insumo(
    db: AsyncSession, detalle: RecetaDetalleInsumo
) -> RecetaDetalleInsumo:
    db.add(detalle)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def update_detalle_insumo(
    db: AsyncSession, detalle: RecetaDetalleInsumo, data: dict
) -> RecetaDetalleInsumo:
    for key, value in data.items():
        setattr(detalle, key, value)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def delete_detalle_insumo(
    db: AsyncSession, detalle: RecetaDetalleInsumo
) -> None:
    await db.delete(detalle)
    await db.flush()


# ── RecetaDetalleSubreceta ────────────────────────────────────────────────────

async def get_detalle_subreceta_by_id(
    db: AsyncSession, detalle_id: int
) -> RecetaDetalleSubreceta | None:
    return await db.get(RecetaDetalleSubreceta, detalle_id)


async def create_detalle_subreceta(
    db: AsyncSession, detalle: RecetaDetalleSubreceta
) -> RecetaDetalleSubreceta:
    db.add(detalle)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def update_detalle_subreceta(
    db: AsyncSession, detalle: RecetaDetalleSubreceta, data: dict
) -> RecetaDetalleSubreceta:
    for key, value in data.items():
        setattr(detalle, key, value)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def delete_detalle_subreceta(
    db: AsyncSession, detalle: RecetaDetalleSubreceta
) -> None:
    await db.delete(detalle)
    await db.flush()


# ── RecetaPaso ────────────────────────────────────────────────────────────────

async def get_paso_by_id(db: AsyncSession, paso_id: int) -> RecetaPaso | None:
    return await db.get(RecetaPaso, paso_id)


async def create_paso(db: AsyncSession, paso: RecetaPaso) -> RecetaPaso:
    db.add(paso)
    await db.flush()
    await db.refresh(paso)
    return paso


async def update_paso(
    db: AsyncSession, paso: RecetaPaso, data: dict
) -> RecetaPaso:
    for key, value in data.items():
        setattr(paso, key, value)
    await db.flush()
    await db.refresh(paso)
    return paso


async def delete_paso(db: AsyncSession, paso: RecetaPaso) -> None:
    await db.delete(paso)
    await db.flush()
