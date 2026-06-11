"""
insumo_repo.py
Async repository for Insumo, Subreceta, and SubrecetaIngrediente.
Uses SQLAlchemy 2.x select() syntax with AsyncSession.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.insumo import Insumo, Subreceta, SubrecetaIngrediente


# ── Insumo ────────────────────────────────────────────────────────────────────

async def get_insumo_by_id(db: AsyncSession, id_insumo: int) -> Insumo | None:
    return await db.get(Insumo, id_insumo)


async def get_insumos(
    db: AsyncSession,
    *,
    solo_activos: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Insumo]:
    query = select(Insumo)
    if solo_activos:
        query = query.where(Insumo.activo.is_(True))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_insumo(db: AsyncSession, insumo: Insumo) -> Insumo:
    db.add(insumo)
    await db.flush()
    await db.refresh(insumo)
    return insumo


async def update_insumo(db: AsyncSession, insumo: Insumo, data: dict) -> Insumo:
    for key, value in data.items():
        setattr(insumo, key, value)
    await db.flush()
    await db.refresh(insumo)
    return insumo


async def delete_insumo(db: AsyncSession, insumo: Insumo) -> None:
    await update_insumo(db, insumo, {"activo": False})


# ── Subreceta ─────────────────────────────────────────────────────────────────

async def get_subreceta_by_id(db: AsyncSession, id_subreceta: int) -> Subreceta | None:
    result = await db.execute(
        select(Subreceta)
        .options(selectinload(Subreceta.ingredientes))
        .where(Subreceta.id_subreceta == id_subreceta)
    )
    return result.scalar_one_or_none()


async def get_subrecetas(
    db: AsyncSession,
    *,
    solo_activos: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[Subreceta]:
    query = select(Subreceta)
    if solo_activos:
        query = query.where(Subreceta.activo.is_(True))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_subreceta(db: AsyncSession, subreceta: Subreceta) -> Subreceta:
    db.add(subreceta)
    await db.flush()
    await db.refresh(subreceta)
    return subreceta


async def update_subreceta(db: AsyncSession, subreceta: Subreceta, data: dict) -> Subreceta:
    for key, value in data.items():
        setattr(subreceta, key, value)
    await db.flush()
    await db.refresh(subreceta)
    return subreceta


async def delete_subreceta(db: AsyncSession, subreceta: Subreceta) -> None:
    await update_subreceta(db, subreceta, {"activo": False})


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

async def get_ingrediente(
    db: AsyncSession, id_subreceta: int, id_insumo: int
) -> SubrecetaIngrediente | None:
    result = await db.execute(
        select(SubrecetaIngrediente).where(
            SubrecetaIngrediente.id_subreceta == id_subreceta,
            SubrecetaIngrediente.id_insumo == id_insumo,
        )
    )
    return result.scalar_one_or_none()


async def get_ingrediente_by_id(
    db: AsyncSession, id_subreceta_ing: int
) -> SubrecetaIngrediente | None:
    return await db.get(SubrecetaIngrediente, id_subreceta_ing)


async def get_ingredientes_by_subreceta(
    db: AsyncSession, id_subreceta: int
) -> list[SubrecetaIngrediente]:
    result = await db.execute(
        select(SubrecetaIngrediente).where(
            SubrecetaIngrediente.id_subreceta == id_subreceta
        )
    )
    return list(result.scalars().all())


async def create_ingrediente(
    db: AsyncSession, ingrediente: SubrecetaIngrediente
) -> SubrecetaIngrediente:
    db.add(ingrediente)
    await db.flush()
    await db.refresh(ingrediente)
    return ingrediente


async def update_ingrediente(
    db: AsyncSession, ingrediente: SubrecetaIngrediente, data: dict
) -> SubrecetaIngrediente:
    for key, value in data.items():
        setattr(ingrediente, key, value)
    await db.flush()
    await db.refresh(ingrediente)
    return ingrediente


async def delete_ingrediente(
    db: AsyncSession, ingrediente: SubrecetaIngrediente
) -> None:
    await db.delete(ingrediente)
    await db.flush()