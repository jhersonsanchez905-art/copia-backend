"""
insumo.py (router)
Async CRUD endpoints for Insumo, Subreceta, and SubrecetaIngrediente.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import insumo_service
from app.schemas.insumo_schema import (
    InsumoCreate,
    InsumoUpdate,
    InsumoResponse,
    SubrecetaCreate,
    SubrecetaUpdate,
    SubrecetaResponse,
    SubrecetaIngredienteCreate,
    SubrecetaIngredienteUpdate,
    SubrecetaIngredienteResponse,
)

router = APIRouter()


# ── Insumo ────────────────────────────────────────────────────────────────────

@router.get("/insumos", response_model=list[InsumoResponse], tags=["Insumos"])
async def listar_insumos(
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await insumo_service.get_insumos(db, skip=skip, limit=limit, solo_activos=solo_activos)


@router.get("/insumos/{id_insumo}", response_model=InsumoResponse, tags=["Insumos"])
async def obtener_insumo(id_insumo: int, db: AsyncSession = Depends(get_db)):
    return await insumo_service.get_insumo(db, id_insumo)


@router.post(
    "/insumos",
    response_model=InsumoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Insumos"],
)
async def crear_insumo(data: InsumoCreate, db: AsyncSession = Depends(get_db)):
    return await insumo_service.create_insumo(db, data)


@router.patch("/insumos/{id_insumo}", response_model=InsumoResponse, tags=["Insumos"])
async def actualizar_insumo(
    id_insumo: int, data: InsumoUpdate, db: AsyncSession = Depends(get_db)
):
    return await insumo_service.update_insumo(db, id_insumo, data)


@router.delete(
    "/insumos/{id_insumo}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Insumos"],
)
async def eliminar_insumo(id_insumo: int, db: AsyncSession = Depends(get_db)):
    await insumo_service.delete_insumo(db, id_insumo)


# ── Subreceta ─────────────────────────────────────────────────────────────────

@router.get("/subrecetas", response_model=list[SubrecetaResponse], tags=["Subrecetas"])
async def listar_subrecetas(
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await insumo_service.get_subrecetas(db, skip=skip, limit=limit, solo_activos=solo_activos)


@router.get("/subrecetas/{id_subreceta}", response_model=SubrecetaResponse, tags=["Subrecetas"])
async def obtener_subreceta(id_subreceta: int, db: AsyncSession = Depends(get_db)):
    return await insumo_service.get_subreceta(db, id_subreceta)


@router.post(
    "/subrecetas",
    response_model=SubrecetaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Subrecetas"],
)
async def crear_subreceta(data: SubrecetaCreate, db: AsyncSession = Depends(get_db)):
    return await insumo_service.create_subreceta(db, data)


@router.patch(
    "/subrecetas/{id_subreceta}", response_model=SubrecetaResponse, tags=["Subrecetas"]
)
async def actualizar_subreceta(
    id_subreceta: int, data: SubrecetaUpdate, db: AsyncSession = Depends(get_db)
):
    return await insumo_service.update_subreceta(db, id_subreceta, data)


@router.delete(
    "/subrecetas/{id_subreceta}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Subrecetas"],
)
async def eliminar_subreceta(id_subreceta: int, db: AsyncSession = Depends(get_db)):
    await insumo_service.delete_subreceta(db, id_subreceta)


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

@router.get(
    "/subrecetas/{id_subreceta}/ingredientes",
    response_model=list[SubrecetaIngredienteResponse],
    tags=["Subrecetas"],
)
async def listar_ingredientes(id_subreceta: int, db: AsyncSession = Depends(get_db)):
    return await insumo_service.get_ingredientes_by_subreceta(db, id_subreceta)


@router.post(
    "/subrecetas/ingredientes",
    response_model=SubrecetaIngredienteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Subrecetas"],
)
async def crear_ingrediente(
    data: SubrecetaIngredienteCreate, db: AsyncSession = Depends(get_db)
):
    return await insumo_service.create_ingrediente(db, data)


@router.patch(
    "/subrecetas/ingredientes/{id_subreceta_ing}",
    response_model=SubrecetaIngredienteResponse,
    tags=["Subrecetas"],
)
async def actualizar_ingrediente(
    id_subreceta_ing: int,
    data: SubrecetaIngredienteUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await insumo_service.update_ingrediente(db, id_subreceta_ing, data)


@router.delete(
    "/subrecetas/ingredientes/{id_subreceta_ing}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Subrecetas"],
)
async def eliminar_ingrediente(
    id_subreceta_ing: int, db: AsyncSession = Depends(get_db)
):
    await insumo_service.delete_ingrediente(db, id_subreceta_ing)
