"""
venta_service.py
Async business logic for Venta registration with atomic inventory deduction.

Flow for registrar_venta:
0. Validate pedido state and apertura is open.
1. Resolve active RecetaVersion for each product.
2. Aggregate insumo quantities across all items (Insumo + Subreceta ingredients).
3. Verify ALL stocks before touching anything.
4. Create Venta + ItemVenta records with receta_snapshot.
5. Deduct stock for each insumo, create MovimientoInventario, evaluate semaforo.
6. Create Pago and Factura records.
7. Mark Pedido as 'pagado', mark Mesa as 'disponible'.
8. Commit atomically — any failure rolls back.
"""
import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import InsumoInsuficienteError, MajesaError, VentaNoEncontradaError
from app.models.insumo import Subreceta
from app.models.pedido import PedidoServicio
from app.models.venta import Factura, ItemVenta, Pago, Venta
from app.repositories import caja_repo, pedido_repo, producto_repo, receta_repo, stock_repo, venta_repo
from app.schemas.venta_schema import VentaCreateRequest
from app.services import inventario_service


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def _get_subreceta_with_ingredients(
    db: AsyncSession, id_subreceta: int
) -> Subreceta | None:
    result = await db.execute(
        select(Subreceta)
        .options(selectinload(Subreceta.ingredientes))
        .where(Subreceta.id_subreceta == id_subreceta)
    )
    return result.scalar_one_or_none()


def _build_snapshot(version) -> dict[str, Any]:
    return {
        "id_receta_version": version.id_receta_version,
        "version": version.version,
        "detalles_insumo": [
            {
                "id_receta_detalle_insumo": d.id_receta_detalle_insumo,
                "id_insumo": d.id_insumo,
                "cantidad": str(d.cantidad),
                "id_unidad": d.id_unidad,
            }
            for d in version.detalles_insumo
        ],
        "detalles_subreceta": [
            {
                "id_receta_detalle_subreceta": d.id_receta_detalle_subreceta,
                "id_subreceta": d.id_subreceta,
                "cantidad": str(d.cantidad),
                "id_unidad": d.id_unidad,
            }
            for d in version.detalles_subreceta
        ],
    }


async def registrar_venta(
    data: VentaCreateRequest,
    id_usuario: int,
    db: AsyncSession,
) -> Venta:
    """
    Registers a sale with full atomic inventory deduction.
    Raises InsumoInsuficienteError if any ingredient has insufficient stock.
    Raises MajesaError(404) if product has no active recipe.
    All DB operations committed in one transaction; any error rolls back.
    """
    try:
        # ── Step 0: pre-flight validations ───────────────────────────────────

        # Validate pedido exists and is in 'enviado' state (RF-020 / 1.3)
        pedido = None
        if data.id_pedido is not None:
            pedido = await pedido_repo.get_pedido_with_mesa(db, data.id_pedido)
            if not pedido:
                raise MajesaError(f"Pedido {data.id_pedido} no encontrado", 404)
            if pedido.estado != "enviado":
                raise MajesaError(
                    "El pedido debe estar en estado enviado para registrar venta", 422
                )

        # Block sales against a closed apertura (1.4)
        if await caja_repo.get_cierre_by_apertura(data.id_apertura, db):
            raise MajesaError(
                "No se pueden registrar ventas en una apertura ya cerrada", 409
            )

        # ── Step 1 & 2: resolve recipes and aggregate insumo requirements ────
        # {id_insumo: Decimal total_needed}
        requerimientos: dict[int, Decimal] = {}
        # Per item: (version, snapshot, precio_unitario, cantidad)
        items_info = []

        for item_req in data.productos:
            version = await receta_repo.get_vigente_by_producto(db, item_req.id_producto)
            if not version:
                raise MajesaError(
                    f"Producto {item_req.id_producto} no tiene receta vigente", 422
                )

            # Direct insumos
            for detalle in version.detalles_insumo:
                needed = detalle.cantidad * item_req.cantidad
                requerimientos[detalle.id_insumo] = (
                    requerimientos.get(detalle.id_insumo, Decimal("0")) + needed
                )

            # Subreceta ingredients
            for det_sub in version.detalles_subreceta:
                subreceta = await _get_subreceta_with_ingredients(db, det_sub.id_subreceta)
                if not subreceta:
                    continue
                porciones = Decimal(subreceta.porciones or 1)
                for ing in subreceta.ingredientes:
                    needed = det_sub.cantidad * item_req.cantidad * ing.cantidad / porciones
                    requerimientos[ing.id_insumo] = (
                        requerimientos.get(ing.id_insumo, Decimal("0")) + needed
                    )

            # Get product price from Producto model
            producto = await producto_repo.get_by_id(db, item_req.id_producto)
            precio_unitario = producto.precio if producto else Decimal("0")
            snapshot = _build_snapshot(version)
            items_info.append((version, snapshot, precio_unitario, item_req.cantidad))

        # ── Step 3: verify all stocks before touching anything ───────────────
        for id_insumo, cantidad_requerida in requerimientos.items():
            stock = await stock_repo.get_stock_by_insumo(db, id_insumo)
            if stock is None or stock.cantidad < cantidad_requerida:
                disponible = stock.cantidad if stock else Decimal("0")
                raise InsumoInsuficienteError(
                    f"Stock insuficiente para insumo {id_insumo}: "
                    f"disponible={disponible}, requerido={cantidad_requerida}"
                )

        # ── Step 4: create Venta ─────────────────────────────────────────────
        subtotal = sum(precio * qty for _, _, precio, qty in items_info)

        if data.id_pedido is not None:
            servicios_result = await db.execute(
                select(PedidoServicio).where(PedidoServicio.id_pedido == data.id_pedido)
            )
            subtotal += sum(s.subtotal for s in servicios_result.scalars().all())

        total_pagado = sum(p.monto for p in data.pagos)
        if total_pagado < subtotal:
            raise MajesaError(
                f"Pago insuficiente: total={subtotal}, pagado={total_pagado}", 422
            )

        venta = Venta(
            id_apertura=data.id_apertura,
            id_pedido=data.id_pedido,
            id_usuario=id_usuario,
            id_cliente=data.id_cliente,
            turno=data.turno,
            fecha=_now(),
            subtotal=subtotal,
            total=total_pagado,
            estado="completada",
        )
        venta = await venta_repo.create_venta(venta, db)

        # ── Step 4b: create ItemVenta records ────────────────────────────────
        for version, snapshot, precio_unitario, cantidad in items_info:
            item = ItemVenta(
                id_venta=venta.id_venta,
                id_producto=version.id_producto,
                id_receta_version=version.id_receta_version,
                receta_snapshot=snapshot,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad,
            )
            await venta_repo.create_item_venta(item, db)

        # ── Step 5: deduct stock, create movements, evaluate semaforo ────────
        for id_insumo, cantidad_requerida in requerimientos.items():
            await inventario_service.descontar_stock(
                db,
                id_insumo=id_insumo,
                cantidad=cantidad_requerida,
                id_usuario=id_usuario,
                id_venta=venta.id_venta,
                motivo="salida por venta",
            )

        # ── Step 6: create Pago and Factura ───────────────────────────────────
        for pago_data in data.pagos:
            pago = Pago(
                id_venta=venta.id_venta,
                id_metodo_pago=pago_data.id_metodo_pago,
                monto=pago_data.monto,
                url_comprobante=pago_data.url_comprobante,
                estado_validacion="pendiente",
            )
            await venta_repo.create_pago(pago, db)

        factura = Factura(
            id_venta=venta.id_venta,
            numero=f"FAC-{venta.id_venta:06d}",
            fecha_emision=_now(),
            total=total_pagado,
        )
        await venta_repo.create_factura(factura, db)

        # ── Step 7: update Pedido estado → pagado; Mesa → disponible ─────────
        # Reuse the pedido already fetched in step 0 (no extra query)
        if pedido:
            pedido.estado = "pagado"
            if pedido.mesa:
                pedido.mesa.estado = "disponible"

        await db.commit()

        return await venta_repo.get_venta_by_id(venta.id_venta, db)

    except Exception:
        await db.rollback()
        raise


async def get_venta_by_id(id_venta: int, db: AsyncSession) -> Venta:
    venta = await venta_repo.get_venta_by_id(id_venta, db)
    if not venta:
        raise VentaNoEncontradaError(id_venta)
    return venta


async def get_ventas_by_fecha_turno(
    fecha,
    turno: str | None,
    db: AsyncSession,
) -> list[Venta]:
    return await venta_repo.get_ventas_by_fecha_turno(fecha, turno, db)
