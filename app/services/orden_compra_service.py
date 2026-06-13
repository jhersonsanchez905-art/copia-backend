"""
orden_compra_service.py
Async business logic for OrdenCompra and OrdenCompraDetalle.
State machine: BORRADOR → ENVIADA → RECIBIDA_PARCIAL/TOTAL | CANCELADA
"""
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.orden_compra import EstadoOrdenCompra
from app.repositories import orden_compra_repo
from app.schemas.orden_compra_schema import (
    OrdenCompraCreate,
    OrdenCompraDetalleCreate,
    OrdenCompraDetalleUpdate,
    OrdenCompraUpdate,
)
from app.services import inventario_service

_TRANSITIONS: dict[EstadoOrdenCompra, set[EstadoOrdenCompra]] = {
    EstadoOrdenCompra.BORRADOR: {EstadoOrdenCompra.ENVIADA, EstadoOrdenCompra.CANCELADA},
    EstadoOrdenCompra.ENVIADA: {
        EstadoOrdenCompra.RECIBIDA_PARCIAL,
        EstadoOrdenCompra.RECIBIDA_TOTAL,
        EstadoOrdenCompra.CANCELADA,
    },
    EstadoOrdenCompra.RECIBIDA_PARCIAL: {EstadoOrdenCompra.RECIBIDA_TOTAL},
    EstadoOrdenCompra.RECIBIDA_TOTAL: set(),
    EstadoOrdenCompra.CANCELADA: set(),
}

_ESTADOS_RECIBIDA = {EstadoOrdenCompra.RECIBIDA_PARCIAL, EstadoOrdenCompra.RECIBIDA_TOTAL}


async def get_orden_compra(db: AsyncSession, id_orden_compra: int):
    orden = await orden_compra_repo.get_orden_compra(db, id_orden_compra)
    if not orden:
        raise MajesaError("Orden de compra no encontrada", 404)
    return orden


async def get_ordenes_compra(db: AsyncSession, skip: int = 0, limit: int = 100):
    return await orden_compra_repo.get_ordenes_compra(db, skip, limit)


async def create_orden_compra(db: AsyncSession, data: OrdenCompraCreate):
    orden = await orden_compra_repo.create_orden_compra(db, data)
    await db.commit()
    return await orden_compra_repo.get_orden_compra(db, orden.id_orden_compra)


async def update_orden_compra(
    db: AsyncSession, id_orden_compra: int, data: OrdenCompraUpdate, id_usuario: int
):
    orden = await get_orden_compra(db, id_orden_compra)
    update_data = data.model_dump(exclude_unset=True)

    if "estado" in update_data and update_data["estado"] is not None:
        nuevo_estado = update_data["estado"]
        allowed = _TRANSITIONS.get(orden.estado, set())
        if nuevo_estado not in allowed:
            allowed_labels = [e.value for e in allowed] or ["ninguna"]
            raise MajesaError(
                f"Transición inválida: {orden.estado.value!r} → {nuevo_estado.value!r}. "
                f"Permitidas desde este estado: {allowed_labels}",
                409,
            )

        # Ingest stock only on first receive (ENVIADA → RECIBIDA_*)
        if nuevo_estado in _ESTADOS_RECIBIDA and orden.estado == EstadoOrdenCompra.ENVIADA:
            detalles = await orden_compra_repo.get_detalles_by_orden(db, id_orden_compra)
            for detalle in detalles:
                if detalle.cantidad_recibida and detalle.cantidad_recibida > 0:
                    await inventario_service.ingresar_stock(
                        db,
                        id_insumo=detalle.id_insumo,
                        cantidad=Decimal(str(detalle.cantidad_recibida)),
                        id_usuario=id_usuario,
                        id_orden_compra=id_orden_compra,
                        motivo=f"Recepción orden #{orden.numero_orden}",
                    )

    await orden_compra_repo.update_orden_compra(db, orden, update_data)
    await db.commit()
    return await orden_compra_repo.get_orden_compra(db, id_orden_compra)


async def delete_orden_compra(db: AsyncSession, id_orden_compra: int):
    """Cancel an order (soft-delete: sets estado = CANCELADA)."""
    orden = await get_orden_compra(db, id_orden_compra)
    if orden.estado == EstadoOrdenCompra.CANCELADA:
        raise MajesaError("La orden ya está cancelada", 409)
    allowed = _TRANSITIONS.get(orden.estado, set())
    if EstadoOrdenCompra.CANCELADA not in allowed:
        raise MajesaError(
            f"No se puede cancelar una orden en estado {orden.estado.value!r}", 400
        )
    await orden_compra_repo.update_orden_compra(
        db, orden, {"estado": EstadoOrdenCompra.CANCELADA}
    )
    await db.commit()
    return await orden_compra_repo.get_orden_compra(db, id_orden_compra)


async def get_detalles_by_orden(db: AsyncSession, id_orden_compra: int):
    await get_orden_compra(db, id_orden_compra)
    return await orden_compra_repo.get_detalles_by_orden(db, id_orden_compra)


async def create_detalle(
    db: AsyncSession, id_orden_compra: int, data: OrdenCompraDetalleCreate
):
    orden = await get_orden_compra(db, id_orden_compra)
    if orden.estado != EstadoOrdenCompra.BORRADOR:
        raise MajesaError(
            "Solo se pueden agregar detalles a órdenes en estado BORRADOR", 400
        )
    detalle = await orden_compra_repo.create_detalle(db, id_orden_compra, data)
    await db.commit()
    return detalle


async def update_detalle(
    db: AsyncSession, id_detalle: int, data: OrdenCompraDetalleUpdate
):
    detalle = await orden_compra_repo.get_detalle(db, id_detalle)
    if not detalle:
        raise MajesaError("Detalle no encontrado", 404)
    update_data = data.model_dump(exclude_unset=True)
    detalle = await orden_compra_repo.update_detalle(db, detalle, update_data)
    await db.commit()
    return detalle


async def delete_detalle(db: AsyncSession, id_detalle: int) -> None:
    detalle = await orden_compra_repo.get_detalle(db, id_detalle)
    if not detalle:
        raise MajesaError("Detalle no encontrado", 404)
    await orden_compra_repo.delete_detalle(db, detalle)
    await db.commit()
