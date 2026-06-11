"""
insumo_service.py
Async business logic for Insumo, Subreceta, and SubrecetaIngrediente.
"""
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.insumo import Insumo, Subreceta, SubrecetaIngrediente
from app.models.receta import RecetaDetalleInsumo, RecetaDetalleSubreceta, RecetaVersion
from app.repositories import insumo_repo
from app.schemas.insumo_schema import (
    InsumoCreate,
    InsumoUpdate,
    SubrecetaCreate,
    SubrecetaUpdate,
    SubrecetaIngredienteCreate,
    SubrecetaIngredienteUpdate,
)


# ── Insumo ────────────────────────────────────────────────────────────────────

async def get_insumo(db: AsyncSession, id_insumo: int) -> Insumo:
    insumo = await insumo_repo.get_insumo_by_id(db, id_insumo)
    if not insumo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Insumo no encontrado")
    return insumo


async def get_insumos(
    db: AsyncSession, skip: int = 0, limit: int = 100, solo_activos: bool = False
) -> list[Insumo]:
    return await insumo_repo.get_insumos(db, solo_activos=solo_activos, skip=skip, limit=limit)


async def create_insumo(db: AsyncSession, data: InsumoCreate) -> Insumo:
    insumo = Insumo(**data.model_dump())
    insumo = await insumo_repo.create_insumo(db, insumo)
    await db.commit()
    return insumo


async def update_insumo(db: AsyncSession, id_insumo: int, data: InsumoUpdate) -> Insumo:
    insumo = await get_insumo(db, id_insumo)
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No hay campos para actualizar")
    insumo = await insumo_repo.update_insumo(db, insumo, fields)
    await db.commit()
    return insumo


async def delete_insumo(db: AsyncSession, id_insumo: int) -> None:
    insumo = await get_insumo(db, id_insumo)
    count = await db.scalar(
        select(func.count()).where(RecetaDetalleInsumo.id_insumo == id_insumo)
    )
    if count:
        raise MajesaError(f"El insumo está en uso en {count} detalle(s) de receta", 409)
    await insumo_repo.delete_insumo(db, insumo)
    await db.commit()


# ── Subreceta ─────────────────────────────────────────────────────────────────

async def get_subreceta(db: AsyncSession, id_subreceta: int) -> Subreceta:
    subreceta = await insumo_repo.get_subreceta_by_id(db, id_subreceta)
    if not subreceta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Subreceta no encontrada")
    return subreceta


async def get_subrecetas(
    db: AsyncSession, skip: int = 0, limit: int = 100, solo_activos: bool = False
) -> list[Subreceta]:
    return await insumo_repo.get_subrecetas(db, solo_activos=solo_activos, skip=skip, limit=limit)


async def create_subreceta(db: AsyncSession, data: SubrecetaCreate) -> Subreceta:
    subreceta = Subreceta(**data.model_dump())
    subreceta = await insumo_repo.create_subreceta(db, subreceta)
    await db.commit()
    return subreceta


async def update_subreceta(
    db: AsyncSession, id_subreceta: int, data: SubrecetaUpdate
) -> Subreceta:
    subreceta = await get_subreceta(db, id_subreceta)
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No hay campos para actualizar")
    subreceta = await insumo_repo.update_subreceta(db, subreceta, fields)

    if "costo_total" in fields or "porciones" in fields:
        from app.services.receta_service import _calcular_costo_version

        res = await db.execute(
            select(RecetaDetalleSubreceta.id_receta_version)
            .where(RecetaDetalleSubreceta.id_subreceta == id_subreceta)
            .distinct()
        )
        for (vid,) in res.all():
            rv = await db.get(RecetaVersion, vid)
            if rv:
                rv.costo_total = await _calcular_costo_version(db, vid)

    await db.commit()
    return subreceta


async def delete_subreceta(db: AsyncSession, id_subreceta: int) -> None:
    subreceta = await get_subreceta(db, id_subreceta)
    count = await db.scalar(
        select(func.count()).where(RecetaDetalleSubreceta.id_subreceta == id_subreceta)
    )
    if count:
        raise MajesaError(f"La subreceta está en uso en {count} receta(s)", 409)
    await insumo_repo.delete_subreceta(db, subreceta)
    await db.commit()


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

async def get_ingredientes_by_subreceta(
    db: AsyncSession, id_subreceta: int
) -> list[SubrecetaIngrediente]:
    await get_subreceta(db, id_subreceta)
    return await insumo_repo.get_ingredientes_by_subreceta(db, id_subreceta)


async def create_ingrediente(
    db: AsyncSession, data: SubrecetaIngredienteCreate
) -> SubrecetaIngrediente:
    await get_subreceta(db, data.id_subreceta)
    existing = await insumo_repo.get_ingrediente(db, data.id_subreceta, data.id_insumo)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="El ingrediente ya existe en esta subreceta")
    ingrediente = SubrecetaIngrediente(**data.model_dump())
    ingrediente = await insumo_repo.create_ingrediente(db, ingrediente)
    await db.commit()
    return ingrediente


async def update_ingrediente(
    db: AsyncSession,
    id_subreceta_ing: int,
    data: SubrecetaIngredienteUpdate,
) -> SubrecetaIngrediente:
    ingrediente = await insumo_repo.get_ingrediente_by_id(db, id_subreceta_ing)
    if not ingrediente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ingrediente no encontrado")
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No hay campos para actualizar")
    ingrediente = await insumo_repo.update_ingrediente(db, ingrediente, fields)
    await db.commit()
    return ingrediente


async def delete_ingrediente(db: AsyncSession, id_subreceta_ing: int) -> None:
    ingrediente = await insumo_repo.get_ingrediente_by_id(db, id_subreceta_ing)
    if not ingrediente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ingrediente no encontrado")
    await insumo_repo.delete_ingrediente(db, ingrediente)
    await db.commit()
