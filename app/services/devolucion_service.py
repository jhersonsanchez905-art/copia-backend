"""
devolucion_service.py
Async business logic for Devolucion (returns).
States: pendiente → aprobada | rechazada

<<<<<<< HEAD
Author: Jherson
=======
Author: SebasValero12
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
Issue: #40
"""
import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.venta import Devolucion
from app.repositories import devolucion_repo
from app.schemas.devolucion_schema import DevolucionCreate
from app.services import inventario_service


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── Queries ───────────────────────────────────────────────────────────────────

async def get_devolucion(db: AsyncSession, id_devolucion: int) -> Devolucion:
    devolucion = await devolucion_repo.get_devolucion_by_id(db, id_devolucion)
    if not devolucion:
        raise MajesaError(f"Devolución {id_devolucion} no encontrada", 404)
    return devolucion


async def get_devoluciones(
    db: AsyncSession, estado: str | None = None
) -> list[Devolucion]:
    return await devolucion_repo.get_devoluciones(db, estado=estado)


# ── Crear ─────────────────────────────────────────────────────────────────────

async def crear_devolucion(
    db: AsyncSession, data: DevolucionCreate
) -> Devolucion:
    """
    Create a return for an ItemVenta.
    The associated Venta must be in state 'completada'.
    """
    venta = await devolucion_repo.get_venta_by_id(db, data.id_venta)
    if not venta:
        raise MajesaError(f"Venta {data.id_venta} no encontrada", 404)
    if venta.estado != "completada":
        raise MajesaError(
            f"Solo se pueden crear devoluciones para ventas finalizadas. "
            f"Estado actual: {venta.estado!r}",
            400,
        )

    item_venta = await devolucion_repo.get_item_venta_by_id(
        db, data.id_item_venta
    )
    if not item_venta or item_venta.id_venta != data.id_venta:
        raise MajesaError(
            f"ItemVenta {data.id_item_venta} no encontrado en venta "
            f"{data.id_venta}",
            404,
        )
    if data.cantidad > item_venta.cantidad:
        raise MajesaError(
            f"Cantidad a devolver ({data.cantidad}) excede la cantidad "
            f"vendida ({item_venta.cantidad})",
            400,
        )

    devolucion = Devolucion(
        id_venta=data.id_venta,
        id_item_venta=data.id_item_venta,
        cantidad=data.cantidad,
        motivo=data.motivo,
        observacion=data.observacion,
        estado="pendiente",
        reintegra_stock=1 if data.reintegra_stock else 0,
        fecha=_now(),
    )
    devolucion = await devolucion_repo.create_devolucion(db, devolucion)
    await db.commit()
    return devolucion


# ── Aprobar ───────────────────────────────────────────────────────────────────

async def aprobar_devolucion(
    db: AsyncSession, id_devolucion: int, id_usuario: int
) -> Devolucion:
    """
    Approve a return (admin only).
    If reintegra_stock == true, uses receta_snapshot from ItemVenta to
    call inventario_service.ingresar_stock() for each ingredient and
    creates a MovimientoInventario of type 'entrada'.
    """
    devolucion = await get_devolucion(db, id_devolucion)
    if devolucion.estado != "pendiente":
        raise MajesaError(
            f"Solo se pueden aprobar devoluciones en estado 'pendiente'. "
            f"Estado actual: {devolucion.estado!r}",
            400,
        )

    update_data: dict = {
        "estado": "aprobada",
        "id_aprobador": id_usuario,
    }

    if devolucion.reintegra_stock:
        item_venta = await devolucion_repo.get_item_venta_by_id(
            db, devolucion.id_item_venta
        )
        if item_venta and item_venta.receta_snapshot:
            snapshot = item_venta.receta_snapshot
            cantidad_devuelta = devolucion.cantidad

            for detalle in snapshot.get("detalles_insumo", []):
                cantidad_insumo = (
                    Decimal(str(detalle["cantidad"])) * cantidad_devuelta
                )
                await inventario_service.ingresar_stock(
                    db,
                    id_insumo=detalle["id_insumo"],
                    cantidad=cantidad_insumo,
                    id_usuario=id_usuario,
                    motivo=f"Reintegro por devolución #{id_devolucion}",
                )

    devolucion = await devolucion_repo.update_devolucion(
        db, devolucion, update_data
    )
    await db.commit()
    return devolucion


# ── Rechazar ──────────────────────────────────────────────────────────────────

async def rechazar_devolucion(
    db: AsyncSession, id_devolucion: int, id_usuario: int
) -> Devolucion:
    """Reject a return (admin only). Does NOT affect inventory."""
    devolucion = await get_devolucion(db, id_devolucion)
    if devolucion.estado != "pendiente":
        raise MajesaError(
            f"Solo se pueden rechazar devoluciones en estado 'pendiente'. "
            f"Estado actual: {devolucion.estado!r}",
            400,
        )
    devolucion = await devolucion_repo.update_devolucion(
        db,
        devolucion,
        {"estado": "rechazada", "id_aprobador": id_usuario},
    )
    await db.commit()
    return devolucion
