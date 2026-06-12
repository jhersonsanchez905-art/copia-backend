"""
orden_compra.py
Endpoints CRUD para órdenes de compra y sus líneas de detalle.
Autor: Ivan Ospino
Issue: #20
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.orden_compra_schema import (
    OrdenCompraCreate,
    OrdenCompraDetalleCreate,
    OrdenCompraDetalleOut,
    OrdenCompraDetalleUpdate,
    OrdenCompraOut,
    OrdenCompraUpdate,
)
from app.services import orden_compra_service

router = APIRouter()


# ── OrdenCompra ───────────────────────────────────────────────────────────────

@router.get("/ordenes-compra", response_model=List[OrdenCompraOut], tags=["Órdenes de Compra"])
async def listar_ordenes_compra(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orden_compra_service.get_ordenes_compra(db, skip, limit)


@router.get("/ordenes-compra/{id_orden_compra}", response_model=OrdenCompraOut, tags=["Órdenes de Compra"])
async def obtener_orden_compra(
    id_orden_compra: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orden_compra_service.get_orden_compra(db, id_orden_compra)


@router.post("/ordenes-compra", response_model=OrdenCompraOut, status_code=201, tags=["Órdenes de Compra"])
async def crear_orden_compra(
    data: OrdenCompraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await orden_compra_service.create_orden_compra(db, data)


@router.patch("/ordenes-compra/{id_orden_compra}", response_model=OrdenCompraOut, tags=["Órdenes de Compra"])
async def actualizar_orden_compra(
    id_orden_compra: int,
    data: OrdenCompraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await orden_compra_service.update_orden_compra(
        db, id_orden_compra, data, current_user.id_usuario
    )


@router.delete("/ordenes-compra/{id_orden_compra}", response_model=OrdenCompraOut, tags=["Órdenes de Compra"])
async def cancelar_orden_compra(
    id_orden_compra: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await orden_compra_service.delete_orden_compra(db, id_orden_compra)


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

@router.get("/ordenes-compra/{id_orden_compra}/detalles", response_model=List[OrdenCompraDetalleOut], tags=["Órdenes de Compra"])
async def listar_detalles(
    id_orden_compra: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await orden_compra_service.get_detalles_by_orden(db, id_orden_compra)


@router.post("/ordenes-compra/{id_orden_compra}/detalles", response_model=OrdenCompraDetalleOut, status_code=201, tags=["Órdenes de Compra"])
async def crear_detalle(
    id_orden_compra: int,
    data: OrdenCompraDetalleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await orden_compra_service.create_detalle(db, id_orden_compra, data)


@router.patch("/ordenes-compra/detalles/{id_detalle}", response_model=OrdenCompraDetalleOut, tags=["Órdenes de Compra"])
async def actualizar_detalle(
    id_detalle: int,
    data: OrdenCompraDetalleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await orden_compra_service.update_detalle(db, id_detalle, data)


@router.delete("/ordenes-compra/detalles/{id_detalle}", status_code=204, tags=["Órdenes de Compra"])
async def eliminar_detalle(
    id_detalle: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    await orden_compra_service.delete_detalle(db, id_detalle)
