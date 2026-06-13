"""
pedido.py (router)
Endpoints for Pedido, PedidoItem, and PedidoServicio.
Mesero flow: abierto → enviado → pagado | cancelado
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.pedido_schema import (
    PedidoCreate,
    PedidoResponse,
    PedidoItemCreate,
    PedidoItemResponse,
)
from app.services import pedido_service

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("", response_model=list[PedidoResponse])
async def listar_pedidos(
    estado: str | None = Query(None),
    id_mesa: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await pedido_service.get_pedidos(db, estado=estado, id_mesa=id_mesa)


@router.get("/{id_pedido}", response_model=PedidoResponse)
async def obtener_pedido(
    id_pedido: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await pedido_service.get_pedido(db, id_pedido)


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    data: PedidoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("cajero", "mesero", "administrador")),
):
    return await pedido_service.create_pedido(db, data, current_user.id_usuario)


@router.patch("/{id_pedido}/estado", response_model=PedidoResponse)
async def cambiar_estado_pedido(
    id_pedido: int,
    nuevo_estado: str = Query(..., description="enviado | cancelado"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("cajero", "mesero", "administrador")),
):
    return await pedido_service.cambiar_estado_pedido(db, id_pedido, nuevo_estado)


@router.post(
    "/{id_pedido}/items",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def agregar_item(
    id_pedido: int,
    data: PedidoItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("mesero", "administrador")),
):
    return await pedido_service.agregar_item(db, id_pedido, data)


@router.patch("/items/{id_pedido_item}/estado", response_model=PedidoItemResponse)
async def cambiar_estado_item(
    id_pedido_item: int,
    nuevo_estado: str = Query(
        ..., description="en_preparacion | listo | entregado | cancelado"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("mesero", "administrador")),
):
    return await pedido_service.cambiar_estado_item(db, id_pedido_item, nuevo_estado)

@router.delete(
    "/{id_pedido}/items/{id_pedido_item}",
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK,
)
async def eliminar_item(
    id_pedido: int,
    id_pedido_item: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("mesero", "administrador")),
):
    return await pedido_service.eliminar_item(db, id_pedido, id_pedido_item)