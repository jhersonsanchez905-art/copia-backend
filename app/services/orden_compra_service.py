"""
orden_compra_service.py
Lógica de negocio para órdenes de compra.

Estados y transiciones permitidas:
  borrador  → enviada    (enviar)
  borrador  → cancelada  (cancelar)
  enviada   → recibida   (recibir)
  enviada   → cancelada  (cancelar)

Al recibir:
  - Actualiza cantidad_recibida de cada detalle indicado.
  - Llama inventario_service.ingresar_stock() por cada línea.
  - El MovimientoInventario queda creado dentro de ingresar_stock con id_orden_compra.
  - Resuelve alertas de stock (Alerta) relacionadas al insumo si las hay.
  - Cambia estado a recibida.

Toda modificación de stock se hace ÚNICAMENTE mediante:
  inventario_service.ingresar_stock()
  inventario_service.descontar_stock()

Autor: Ivan Ospino
Issue: #21
"""

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.orden_compra import EstadoOrdenCompra, OrdenCompra
from app.repositories import orden_compra_repo
from app.schemas.orden_compra_schema import OrdenCompraCreate, OrdenCompraRecibir
from app.services import inventario_service

# Transiciones de estado válidas
_TRANSICIONES: dict[str, list[str]] = {
    EstadoOrdenCompra.borrador:  [EstadoOrdenCompra.enviada,  EstadoOrdenCompra.cancelada],
    EstadoOrdenCompra.enviada:   [EstadoOrdenCompra.recibida, EstadoOrdenCompra.cancelada],
    EstadoOrdenCompra.recibida:  [],
    EstadoOrdenCompra.cancelada: [],
}


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _validar_transicion(orden: OrdenCompra, nuevo_estado: str) -> None:
    permitidos = _TRANSICIONES.get(orden.estado, [])
    if nuevo_estado not in permitidos:
        raise MajesaError(
            f"Transición inválida: '{orden.estado}' → '{nuevo_estado}'. "
            f"Transiciones permitidas desde '{orden.estado}': {permitidos or 'ninguna'}.",
            400,
        )


# ── Consultas ─────────────────────────────────────────────────────────────────

async def get_orden_compra(db: AsyncSession, id_orden_compra: int) -> OrdenCompra:
    orden = await orden_compra_repo.get_orden_compra_by_id(db, id_orden_compra)
    if not orden:
        raise MajesaError(f"OrdenCompra {id_orden_compra} no encontrada", 404)
    return orden


async def get_ordenes_compra(
    db: AsyncSession,
    estado: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[OrdenCompra]:
    return await orden_compra_repo.get_ordenes_compra(db, estado=estado, skip=skip, limit=limit)


# ── Creación ──────────────────────────────────────────────────────────────────

async def create_orden_compra(
    db: AsyncSession, data: OrdenCompraCreate
) -> OrdenCompra:
    orden = await orden_compra_repo.create_orden_compra(db, data)
    await db.commit()
    # Re-fetch con detalles cargados de forma eager (evita MissingGreenlet)
    return await orden_compra_repo.get_orden_compra_by_id(db, orden.id_orden_compra)


# ── Transiciones de estado ────────────────────────────────────────────────────

async def enviar_orden(db: AsyncSession, id_orden_compra: int) -> OrdenCompra:
    orden = await get_orden_compra(db, id_orden_compra)
    _validar_transicion(orden, EstadoOrdenCompra.enviada)

    orden = await orden_compra_repo.update_orden_compra(
        db, orden, {"estado": EstadoOrdenCompra.enviada}
    )
    await db.commit()
    return await orden_compra_repo.get_orden_compra_by_id(db, orden.id_orden_compra)


async def cancelar_orden(db: AsyncSession, id_orden_compra: int) -> OrdenCompra:
    orden = await get_orden_compra(db, id_orden_compra)
    _validar_transicion(orden, EstadoOrdenCompra.cancelada)

    orden = await orden_compra_repo.update_orden_compra(
        db, orden, {"estado": EstadoOrdenCompra.cancelada}
    )
    await db.commit()
    return await orden_compra_repo.get_orden_compra_by_id(db, orden.id_orden_compra)


async def recibir_orden(
    db: AsyncSession,
    id_orden_compra: int,
    data: OrdenCompraRecibir,
    id_usuario: int,
) -> OrdenCompra:
    orden = await get_orden_compra(db, id_orden_compra)
    _validar_transicion(orden, EstadoOrdenCompra.recibida)

    # Actualizar cantidad_recibida y registrar stock por cada línea del payload
    for linea in data.detalles:
        detalle = await orden_compra_repo.get_detalle_by_insumo(
            db, id_orden_compra, linea.id_insumo
        )
        if not detalle:
            raise MajesaError(
                f"No existe detalle para insumo {linea.id_insumo} "
                f"en la orden {id_orden_compra}",
                400,
            )

        # Actualizar cantidad recibida en el detalle
        await orden_compra_repo.update_detalle(
            db, detalle, {"cantidad_recibida": linea.cantidad_recibida}
        )

        # Ingresar stock — crea MovimientoInventario y evalúa semáforo/alertas
        await inventario_service.ingresar_stock(
            db,
            id_insumo=linea.id_insumo,
            cantidad=linea.cantidad_recibida,
            id_usuario=id_usuario,
            id_orden_compra=id_orden_compra,
            motivo=f"Recepción orden de compra #{id_orden_compra}",
        )

    # Cambiar estado y registrar fecha de recepción
    orden = await orden_compra_repo.update_orden_compra(
        db,
        orden,
        {
            "estado": EstadoOrdenCompra.recibida,
            "fecha_recepcion_real": _now().date(),
        },
    )
    await db.commit()
    return await orden_compra_repo.get_orden_compra_by_id(db, orden.id_orden_compra)