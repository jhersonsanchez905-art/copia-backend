"""
pedido_repo.py
Async repository for Pedido, PedidoItem, and PedidoServicio.

Author: Jherson
Issue: #40
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pedido import Pedido, PedidoItem, PedidoServicio


# ── Pedido ────────────────────────────────────────────────────────────────────

async def get_pedido_by_id(db: AsyncSession, id_pedido: int) -> Pedido | None:
    result = await db.execute(
        select(Pedido)
        .options(
            selectinload(Pedido.items),
            selectinload(Pedido.servicios),
        )
        .where(Pedido.id_pedido == id_pedido)
    )
    return result.scalar_one_or_none()


async def get_pedidos(
    db: AsyncSession,
    estado: str | None = None,
    id_mesa: int | None = None,
) -> list[Pedido]:
    query = (
        select(Pedido)
        .options(selectinload(Pedido.items), selectinload(Pedido.servicios))
    )
    if estado:
        query = query.where(Pedido.estado == estado)
    if id_mesa:
        query = query.where(Pedido.id_mesa == id_mesa)
    query = query.order_by(Pedido.fecha_hora.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_pedido(db: AsyncSession, pedido: Pedido) -> Pedido:
    db.add(pedido)
    await db.flush()
    await db.refresh(pedido)
    return pedido


async def update_pedido(db: AsyncSession, pedido: Pedido, data: dict) -> Pedido:
    for key, value in data.items():
        setattr(pedido, key, value)
    await db.flush()
    await db.refresh(pedido)
    return pedido


# ── PedidoItem ────────────────────────────────────────────────────────────────

async def get_pedido_item_by_id(db: AsyncSession, id_item: int) -> PedidoItem | None:
    return await db.get(PedidoItem, id_item)


async def create_pedido_item(db: AsyncSession, item: PedidoItem) -> PedidoItem:
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def update_pedido_item(
    db: AsyncSession, item: PedidoItem, data: dict
) -> PedidoItem:
    for key, value in data.items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_pedido_item(db: AsyncSession, item: PedidoItem) -> None:
    await db.delete(item)
    await db.flush()


# ── PedidoServicio ────────────────────────────────────────────────────────────

async def get_pedido_servicio_by_id(
    db: AsyncSession, id_pedido_servicio: int
) -> PedidoServicio | None:
    return await db.get(PedidoServicio, id_pedido_servicio)


async def create_pedido_servicio(
    db: AsyncSession, servicio: PedidoServicio
) -> PedidoServicio:
    db.add(servicio)
    await db.flush()
    await db.refresh(servicio)
    return servicio


async def delete_pedido_servicio(
    db: AsyncSession, servicio: PedidoServicio
) -> None:
    await db.delete(servicio)
    await db.flush()
