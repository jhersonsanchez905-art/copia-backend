"""
pedido.py (router)
Endpoints for Pedido, PedidoItem, and PedidoServicio.
Mesero flow: abierto → enviado → pagado | cancelado

Author: Jherson / SebasValero12
Issue: #40
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.pedido_schema import (
    PedidoCreate,
    PedidoItemCreate,
    PedidoItemResponse,
    PedidoItemUpdate,
    PedidoResponse,
    PedidoServicioCreate,
    PedidoServicioResponse,
)
from app.services import pedido_service

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


# ── Pedido ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[PedidoResponse])
async def listar_pedidos(
    estado: str | None = Query(None),
    id_mesa: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.get_pedidos(db, estado=estado, id_mesa=id_mesa)


@router.get("/{id_pedido}", response_model=PedidoResponse)
async def obtener_pedido(id_pedido: int, db: AsyncSession = Depends(get_db)):
    return await pedido_service.get_pedido(db, id_pedido)


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def crear_pedido(data: PedidoCreate, db: AsyncSession = Depends(get_db)):
    id_usuario = 1  # TODO: extract from Clerk token
    return await pedido_service.create_pedido(db, data, id_usuario)


@router.patch("/{id_pedido}/estado", response_model=PedidoResponse)
async def cambiar_estado_pedido(
    id_pedido: int,
    nuevo_estado: str = Query(..., description="enviado | cancelado"),
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.cambiar_estado_pedido(db, id_pedido, nuevo_estado)


@router.patch("/{id_pedido}/enviar", response_model=PedidoResponse)
async def enviar_pedido(
    id_pedido: int, db: AsyncSession = Depends(get_db)
):
    return await pedido_service.enviar_pedido(db, id_pedido)


@router.patch("/{id_pedido}/cancelar", response_model=PedidoResponse)
async def cancelar_pedido(
    id_pedido: int, db: AsyncSession = Depends(get_db)
):
    return await pedido_service.cancelar_pedido(db, id_pedido)


# ── Items ─────────────────────────────────────────────────────────────────────

@router.post(
    "/{id_pedido}/items",
    response_model=PedidoItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def agregar_item(
    id_pedido: int,
    data: PedidoItemCreate,
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.agregar_item(db, id_pedido, data)


@router.delete(
    "/{id_pedido}/items/{id_item}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_item(
    id_pedido: int,
    id_item: int,
    db: AsyncSession = Depends(get_db),
):
    await pedido_service.eliminar_item(db, id_pedido, id_item)


@router.patch(
    "/{id_pedido}/items/{id_item}",
    response_model=PedidoItemResponse,
)
async def modificar_item(
    id_pedido: int,
    id_item: int,
    data: PedidoItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.modificar_item(db, id_pedido, id_item, data)


@router.patch("/items/{id_pedido_item}/estado", response_model=PedidoItemResponse)
async def cambiar_estado_item(
    id_pedido_item: int,
    nuevo_estado: str = Query(
        ..., description="en_preparacion | listo | entregado | cancelado"
    ),
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.cambiar_estado_item(db, id_pedido_item, nuevo_estado)


# ── Servicios ─────────────────────────────────────────────────────────────────

@router.post(
    "/{id_pedido}/servicios",
    response_model=PedidoServicioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def agregar_servicio(
    id_pedido: int,
    data: PedidoServicioCreate,
    db: AsyncSession = Depends(get_db),
):
    return await pedido_service.agregar_servicio(db, id_pedido, data)


@router.delete(
    "/{id_pedido}/servicios/{id_servicio}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def eliminar_servicio(
    id_pedido: int,
    id_servicio: int,
    db: AsyncSession = Depends(get_db),
):
    await pedido_service.eliminar_servicio(db, id_pedido, id_servicio)
