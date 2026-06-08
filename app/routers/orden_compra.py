"""
orden_compra.py
Endpoints para gestión de órdenes de compra con máquina de estados.

Transiciones:
  borrador  → enviada    PATCH /ordenes-compra/{id}/enviar
  borrador  → cancelada  PATCH /ordenes-compra/{id}/cancelar
  enviada   → recibida   PATCH /ordenes-compra/{id}/recibir
  enviada   → cancelada  PATCH /ordenes-compra/{id}/cancelar

No se modifica stock directamente — todo pasa por inventario_service.
Autor: Ivan Ospino
Issue: #21
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.orden_compra_schema import (
    EstadoOrdenCompraEnum,
    OrdenCompraCreate,
    OrdenCompraOut,
    OrdenCompraRecibir,
)
from app.services import orden_compra_service

router = APIRouter(prefix="/ordenes-compra", tags=["Órdenes de Compra"])


# ── Consultas ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[OrdenCompraOut])
async def listar_ordenes_compra(
    estado: EstadoOrdenCompraEnum | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await orden_compra_service.get_ordenes_compra(
        db,
        estado=estado.value if estado else None,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_orden_compra}", response_model=OrdenCompraOut)
async def obtener_orden_compra(
    id_orden_compra: int, db: AsyncSession = Depends(get_db)
):
    return await orden_compra_service.get_orden_compra(db, id_orden_compra)


# ── Creación ──────────────────────────────────────────────────────────────────

@router.post("", response_model=OrdenCompraOut, status_code=status.HTTP_201_CREATED)
async def crear_orden_compra(
    data: OrdenCompraCreate, db: AsyncSession = Depends(get_db)
):
    return await orden_compra_service.create_orden_compra(db, data)


# ── Transiciones de estado ────────────────────────────────────────────────────

@router.patch("/{id_orden_compra}/enviar", response_model=OrdenCompraOut)
async def enviar_orden_compra(
    id_orden_compra: int, db: AsyncSession = Depends(get_db)
):
    return await orden_compra_service.enviar_orden(db, id_orden_compra)


@router.patch("/{id_orden_compra}/recibir", response_model=OrdenCompraOut)
async def recibir_orden_compra(
    id_orden_compra: int,
    data: OrdenCompraRecibir,
    db: AsyncSession = Depends(get_db),
):
    # TODO: extraer id_usuario del token Clerk
    id_usuario = 1
    return await orden_compra_service.recibir_orden(db, id_orden_compra, data, id_usuario)


@router.patch("/{id_orden_compra}/cancelar", response_model=OrdenCompraOut)
async def cancelar_orden_compra(
    id_orden_compra: int, db: AsyncSession = Depends(get_db)
):
    return await orden_compra_service.cancelar_orden(db, id_orden_compra)