"""
pedido_service.py
Async business logic for Pedido, PedidoItem, and PedidoServicio.
Mesero flow: abierto → enviado → pagado | cancelado

Author: Jherson / SebasValero12
Issue: #40
"""
import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.mesa import Mesa
from app.models.pedido import Pedido, PedidoItem, PedidoServicio
from app.repositories import mesa_repo, pedido_repo, servicio_adicional_repo
from app.schemas.pedido_schema import (
    PedidoCreate,
    PedidoItemCreate,
    PedidoItemUpdate,
    PedidoServicioCreate,
    PedidoUpdate,
)


_PEDIDO_TRANSITIONS: dict[str, set[str]] = {
    "abierto": {"enviado", "cancelado"},
    "enviado": {"pagado", "cancelado"},
    "pagado": set(),
    "cancelado": set(),
}

_ITEM_TRANSITIONS: dict[str, set[str]] = {
    "pendiente": {"en_preparacion", "cancelado"},
    "en_preparacion": {"listo", "cancelado"},
    "listo": {"entregado"},
    "entregado": set(),
    "cancelado": set(),
}


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _validate_pedido_transition(current: str, next_state: str) -> None:
    allowed = _PEDIDO_TRANSITIONS.get(current, set())
    if next_state not in allowed:
        raise MajesaError(
            f"Transición de pedido inválida: {current!r} → {next_state!r}. "
            f"Permitidas: {sorted(allowed) or 'ninguna'}",
            409,
        )


def _assert_pedido_abierto(pedido: Pedido) -> None:
    if pedido.estado != "abierto":
        raise MajesaError(
            f"Solo se puede modificar un pedido en estado 'abierto'. "
            f"Estado actual: {pedido.estado!r}",
            400,
        )


# ── Pedido ────────────────────────────────────────────────────────────────────

async def get_pedido(db: AsyncSession, id_pedido: int) -> Pedido:
    pedido = await pedido_repo.get_pedido_by_id(db, id_pedido)
    if not pedido:
        raise MajesaError(f"Pedido {id_pedido} no encontrado", 404)
    return pedido


async def get_pedidos(
    db: AsyncSession,
    estado: str | None = None,
    id_mesa: int | None = None,
) -> list[Pedido]:
    return await pedido_repo.get_pedidos(db, estado=estado, id_mesa=id_mesa)


async def create_pedido(
    db: AsyncSession, data: PedidoCreate, id_usuario: int
) -> Pedido:
    mesa = await mesa_repo.get_mesa_by_id(db, data.id_mesa)
    if not mesa:
        raise MajesaError(f"Mesa {data.id_mesa} no encontrada", 404)
    if mesa.estado not in ("disponible", "reservada"):
        raise MajesaError(
            f"No se puede abrir un pedido en mesa {mesa.estado!r}", 409
        )

    pedido = Pedido(
        id_mesa=data.id_mesa,
        id_usuario=id_usuario,
        id_reserva=data.id_reserva,
        observaciones=data.observaciones,
        fecha_hora=_now(),
        estado="abierto",
    )
    pedido = await pedido_repo.create_pedido(db, pedido)

    for item_data in data.items:
        item = PedidoItem(
            id_pedido=pedido.id_pedido,
            id_producto=item_data.id_producto,
            cantidad=item_data.cantidad,
            precio_unitario=item_data.precio_unitario,
            subtotal=item_data.precio_unitario * item_data.cantidad,
            observaciones=item_data.observaciones,
            estado="pendiente",
        )
        await pedido_repo.create_pedido_item(db, item)

    for srv_data in data.servicios:
        servicio = await servicio_adicional_repo.get_servicio_by_id(
            db, srv_data.id_servicio
        )
        if not servicio:
            raise MajesaError(
                f"ServicioAdicional {srv_data.id_servicio} no encontrado", 404
            )
        ps = PedidoServicio(
            id_pedido=pedido.id_pedido,
            id_servicio=srv_data.id_servicio,
            cantidad=srv_data.cantidad,
            valor_unitario=srv_data.valor_unitario,
            subtotal=srv_data.valor_unitario * srv_data.cantidad,
            observaciones=srv_data.observaciones,
        )
        await pedido_repo.create_pedido_servicio(db, ps)

    await mesa_repo.update_mesa(db, mesa, {"estado": "ocupada"})
    await db.commit()
    return await pedido_repo.get_pedido_by_id(db, pedido.id_pedido)


# ── Items ─────────────────────────────────────────────────────────────────────

async def agregar_item(
    db: AsyncSession, id_pedido: int, data: PedidoItemCreate
) -> PedidoItem:
    pedido = await get_pedido(db, id_pedido)
    _assert_pedido_abierto(pedido)
    item = PedidoItem(
        id_pedido=id_pedido,
        id_producto=data.id_producto,
        cantidad=data.cantidad,
        precio_unitario=data.precio_unitario,
        subtotal=data.precio_unitario * data.cantidad,
        observaciones=data.observaciones,
        estado="pendiente",
    )
    item = await pedido_repo.create_pedido_item(db, item)
    await db.commit()
    return item


async def eliminar_item(
    db: AsyncSession, id_pedido: int, id_item: int
) -> None:
    pedido = await get_pedido(db, id_pedido)
    _assert_pedido_abierto(pedido)
    item = await pedido_repo.get_pedido_item_by_id(db, id_item)
    if not item or item.id_pedido != id_pedido:
        raise MajesaError(
            f"PedidoItem {id_item} no encontrado en pedido {id_pedido}", 404
        )
    await pedido_repo.delete_pedido_item(db, item)
    await db.commit()


async def modificar_item(
    db: AsyncSession, id_pedido: int, id_item: int, data: PedidoItemUpdate
) -> PedidoItem:
    pedido = await get_pedido(db, id_pedido)
    _assert_pedido_abierto(pedido)
    item = await pedido_repo.get_pedido_item_by_id(db, id_item)
    if not item or item.id_pedido != id_pedido:
        raise MajesaError(
            f"PedidoItem {id_item} no encontrado en pedido {id_pedido}", 404
        )
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise MajesaError("No hay campos para actualizar", 400)
    if "cantidad" in fields:
        fields["subtotal"] = item.precio_unitario * fields["cantidad"]
    item = await pedido_repo.update_pedido_item(db, item, fields)
    await db.commit()
    return item


async def cambiar_estado_item(
    db: AsyncSession, id_pedido_item: int, nuevo_estado: str
) -> PedidoItem:
    item = await pedido_repo.get_pedido_item_by_id(db, id_pedido_item)
    if not item:
        raise MajesaError(f"PedidoItem {id_pedido_item} no encontrado", 404)
    allowed = _ITEM_TRANSITIONS.get(item.estado, set())
    if nuevo_estado not in allowed:
        raise MajesaError(
            f"Transición de item inválida: {item.estado!r} → {nuevo_estado!r}",
            409,
        )
    item = await pedido_repo.update_pedido_item(
        db, item, {"estado": nuevo_estado}
    )
    await db.commit()
    return item


# ── Servicios ─────────────────────────────────────────────────────────────────

async def agregar_servicio(
    db: AsyncSession, id_pedido: int, data: PedidoServicioCreate
) -> PedidoServicio:
    pedido = await get_pedido(db, id_pedido)
    _assert_pedido_abierto(pedido)
    servicio = await servicio_adicional_repo.get_servicio_by_id(
        db, data.id_servicio
    )
    if not servicio:
        raise MajesaError(
            f"ServicioAdicional {data.id_servicio} no encontrado", 404
        )
    ps = PedidoServicio(
        id_pedido=id_pedido,
        id_servicio=data.id_servicio,
        cantidad=data.cantidad,
        valor_unitario=data.valor_unitario,
        subtotal=data.valor_unitario * data.cantidad,
        observaciones=data.observaciones,
    )
    ps = await pedido_repo.create_pedido_servicio(db, ps)
    await db.commit()
    return ps


async def eliminar_servicio(
    db: AsyncSession, id_pedido: int, id_servicio: int
) -> None:
    pedido = await get_pedido(db, id_pedido)
    _assert_pedido_abierto(pedido)
    ps = await pedido_repo.get_pedido_servicio_by_id(db, id_servicio)
    if not ps or ps.id_pedido != id_pedido:
        raise MajesaError(
            f"PedidoServicio {id_servicio} no encontrado en pedido {id_pedido}",
            404,
        )
    await pedido_repo.delete_pedido_servicio(db, ps)
    await db.commit()


# ── Estado transitions ────────────────────────────────────────────────────────

async def cambiar_estado_pedido(
    db: AsyncSession, id_pedido: int, nuevo_estado: str
) -> Pedido:
    pedido = await get_pedido(db, id_pedido)
    _validate_pedido_transition(pedido.estado, nuevo_estado)
    pedido = await pedido_repo.update_pedido(
        db, pedido, {"estado": nuevo_estado}
    )
    await db.commit()
    return pedido


async def enviar_pedido(db: AsyncSession, id_pedido: int) -> Pedido:
    """abierto → enviado"""
    return await cambiar_estado_pedido(db, id_pedido, "enviado")


async def cancelar_pedido(db: AsyncSession, id_pedido: int) -> Pedido:
    """abierto|enviado → cancelado + mesa → disponible"""
    pedido = await get_pedido(db, id_pedido)
    _validate_pedido_transition(pedido.estado, "cancelado")

    pedido = await pedido_repo.update_pedido(
        db, pedido, {"estado": "cancelado"}
    )

    mesa = await mesa_repo.get_mesa_by_id(db, pedido.id_mesa)
    if mesa and mesa.estado == "ocupada":
        await mesa_repo.update_mesa(db, mesa, {"estado": "disponible"})

    await db.commit()
    return await pedido_repo.get_pedido_by_id(db, pedido.id_pedido)
