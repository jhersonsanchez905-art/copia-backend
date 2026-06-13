"""
venta_service.py
Async business logic for Venta registration with atomic inventory deduction.

Flow for registrar_venta:
0.  Pre-flight validations (apertura, ownership, pedido, mesa, cliente,
    products, payment methods, comprobante).
1.  Resolve active RecetaVersion for each product.
2.  Aggregate insumo quantities across all items (Insumo + Subreceta ingredients).
3.  Verify AND lock all stocks before touching anything (SELECT FOR UPDATE).
4.  Create Venta + ItemVenta records with receta_snapshot.
5.  Deduct stock for each insumo, create MovimientoInventario, evaluate semaforo.
6.  Create Pago and Factura records.
7.  Mark Pedido as 'pagado', mark Mesa as 'disponible'.
8.  Commit atomically — any failure rolls back.
"""
import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy.exc import IntegrityError

from app.exceptions import InsumoInsuficienteError, MajesaError, VentaNoEncontradaError
from app.models.insumo import Subreceta
from app.models.pedido import PedidoServicio
from app.models.venta import Factura, ItemVenta, Pago, Venta
from app.repositories import (
    caja_repo,
    catalogo_repo,
    pedido_repo,
    producto_repo,
    receta_repo,
    stock_repo,
    venta_repo,
)
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


def _build_snapshot(version, nombre_producto: str | None = None) -> dict[str, Any]:
    return {
        "id_receta_version": version.id_receta_version,
        "id_producto": version.id_producto,
        "nombre_producto": nombre_producto,
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
    es_admin: bool = False,
) -> Venta:
    """
    Register a sale with full atomic inventory deduction.
    All DB operations committed in one transaction; any error rolls back.

    When data.token_idempotencia is set, a pre-check returns the existing
    sale immediately if the token was already committed (sequential retry).
    A concurrent duplicate is caught via IntegrityError on the UNIQUE
    constraint and resolved by fetching the winning request's sale.

    Raises:
        MajesaError 404: apertura, pedido, cliente, product, or payment method not found.
        MajesaError 403: cajero trying to use another user's apertura.
        MajesaError 409: apertura closed, pedido already paid, or mesa in wrong state.
        MajesaError 422: inactive product/payment, missing comprobante, bad recipe,
                         insufficient stock, or payment short.
        InsumoInsuficienteError: stock insufficient after locking (should not normally
                                 reach here if step 3 passes, but descontar_stock
                                 double-checks).
    """
    try:
        # ── Step -1: idempotency short-circuit ────────────────────────────────
        # Cheap path for sequential retries: if the token was already committed
        # by a previous request, return the existing sale without re-running any
        # business logic or touching inventory.
        if data.token_idempotencia:
            existing = await venta_repo.get_by_idempotency_token(db, data.token_idempotencia)
            if existing:
                return existing

        # ── Step 0: pre-flight validations ───────────────────────────────────

        # 0a. Apertura must exist
        apertura = await caja_repo.get_apertura_by_id(data.id_apertura, db)
        if not apertura:
            raise MajesaError(f"Apertura {data.id_apertura} no encontrada", 404)

        # 0b. Apertura must still be open
        if await caja_repo.get_cierre_by_apertura(data.id_apertura, db):
            raise MajesaError(
                "No se pueden registrar ventas en una apertura ya cerrada", 409
            )

        # 0c. Non-admin users can only register sales on their own apertura
        if not es_admin and apertura.id_usuario != id_usuario:
            raise MajesaError(
                "Solo puede registrar ventas en su propia apertura de caja", 403
            )

        # 0d-0f. Pedido validations (only when linked to an order)
        pedido = None
        if data.id_pedido is not None:
            pedido = await pedido_repo.get_pedido_with_mesa(db, data.id_pedido)
            if not pedido:
                raise MajesaError(f"Pedido {data.id_pedido} no encontrado", 404)
            if pedido.estado != "enviado":
                raise MajesaError(
                    "El pedido debe estar en estado enviado para registrar venta", 422
                )

            # 0e. Prevent double-payment for the same order
            if await venta_repo.get_venta_completada_by_pedido(db, data.id_pedido):
                raise MajesaError(
                    f"El pedido {data.id_pedido} ya tiene una venta completada", 409
                )

            # 0f. Mesa must be occupied or reserved — not already freed
            if pedido.mesa and pedido.mesa.estado not in {"ocupada", "reservada"}:
                raise MajesaError(
                    f"La mesa {pedido.mesa.numero!r} no está en estado válido para cobro "
                    f"(estado actual: {pedido.mesa.estado!r})",
                    409,
                )

        # 0g. Cliente must exist and be active when provided
        if data.id_cliente is not None:
            cliente = await catalogo_repo.get_cliente_by_id(db, data.id_cliente)
            if not cliente:
                raise MajesaError(f"Cliente {data.id_cliente} no encontrado", 404)
            if not cliente.activo:
                raise MajesaError(f"Cliente {data.id_cliente} no está activo", 422)

        # 0h. Every product must exist and be active — build a map for price resolution
        # (avoids a second per-product query in the recipe loop below)
        productos_map = {}
        for item_req in data.productos:
            if item_req.id_producto in productos_map:
                continue
            producto = await producto_repo.get_by_id(db, item_req.id_producto)
            if not producto:
                raise MajesaError(
                    f"Producto {item_req.id_producto} no encontrado", 404
                )
            if not producto.activo:
                raise MajesaError(
                    f"Producto {item_req.id_producto} ({producto.nombre!r}) no está disponible",
                    422,
                )
            productos_map[item_req.id_producto] = producto

        # 0i. Every payment method must exist, be active, and carry comprobante when required
        for pago_req in data.pagos:
            metodo = await catalogo_repo.get_metodo_pago_by_id(db, pago_req.id_metodo_pago)
            if not metodo:
                raise MajesaError(
                    f"Método de pago {pago_req.id_metodo_pago} no encontrado", 404
                )
            if not metodo.activo:
                raise MajesaError(
                    f"Método de pago {metodo.nombre!r} no está activo", 422
                )
            # Transfer / digital-wallet payments require an uploaded proof
            if metodo.requiere_comprobante and not pago_req.url_comprobante:
                raise MajesaError(
                    f"El método de pago {metodo.nombre!r} requiere comprobante de pago",
                    422,
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

            # Subreceta ingredients — a missing subreceta is a data integrity error
            for det_sub in version.detalles_subreceta:
                subreceta = await _get_subreceta_with_ingredients(db, det_sub.id_subreceta)
                if subreceta is None:
                    raise MajesaError(
                        f"Subreceta {det_sub.id_subreceta} referenciada en la receta del "
                        f"producto {item_req.id_producto} no encontrada",
                        422,
                    )
                porciones = Decimal(str(subreceta.porciones or 1))
                for ing in subreceta.ingredientes:
                    needed = det_sub.cantidad * item_req.cantidad * ing.cantidad / porciones
                    requerimientos[ing.id_insumo] = (
                        requerimientos.get(ing.id_insumo, Decimal("0")) + needed
                    )

            # Price always comes from the database — never from the request payload
            precio_unitario = Decimal(str(productos_map[item_req.id_producto].precio))
            snapshot = _build_snapshot(version, productos_map[item_req.id_producto].nombre)
            items_info.append((version, snapshot, precio_unitario, item_req.cantidad))

        # ── Step 3: lock and verify all stocks before any write ───────────────
        # SELECT ... FOR UPDATE prevents two concurrent transactions from both
        # passing this check and then both deducting, which would cause overselling.
        stocks_map = await stock_repo.get_stocks_by_insumos_for_update(
            db, list(requerimientos.keys())
        )
        for id_insumo, cantidad_requerida in requerimientos.items():
            stock = stocks_map.get(id_insumo)
            if stock is None or stock.cantidad < cantidad_requerida:
                disponible = stock.cantidad if stock else Decimal("0")
                raise InsumoInsuficienteError(
                    f"Stock insuficiente para insumo {id_insumo}: "
                    f"disponible={disponible}, requerido={cantidad_requerida}"
                )

        # ── Step 4: compute totals and create Venta ───────────────────────────
        # subtotal = sum of DB prices × quantities (frontend totals are ignored)
        subtotal = sum(precio * qty for _, _, precio, qty in items_info)

        if data.id_pedido is not None:
            servicios_result = await db.execute(
                select(PedidoServicio).where(PedidoServicio.id_pedido == data.id_pedido)
            )
            subtotal += sum(s.subtotal for s in servicios_result.scalars().all())

        total_pagado = sum(p.monto for p in data.pagos)
        if total_pagado < subtotal:
            raise MajesaError(
                f"Pago insuficiente: requerido={subtotal}, recibido={total_pagado}", 422
            )

        venta = Venta(
            id_apertura=data.id_apertura,
            id_pedido=data.id_pedido,
            id_usuario=id_usuario,              # audit: who processed the sale
            id_cliente=data.id_cliente,
            turno=data.turno,                   # audit: terminal/shift context
            fecha=_now(),                       # audit: exact timestamp
            subtotal=subtotal,
            total=total_pagado,                 # total > subtotal means change was given
            estado="completada",
            token_idempotencia=data.token_idempotencia,
        )
        venta = await venta_repo.create_venta(venta, db)

        # ── Step 4b: create ItemVenta records ─────────────────────────────────
        for version, snapshot, precio_unitario, cantidad in items_info:
            item = ItemVenta(
                id_venta=venta.id_venta,
                id_producto=version.id_producto,
                id_receta_version=version.id_receta_version,
                receta_snapshot=snapshot,   # frozen recipe — survives future recipe changes
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad,
            )
            await venta_repo.create_item_venta(item, db)

        # ── Step 5: deduct stock and create inventory movements ───────────────
        for id_insumo, cantidad_requerida in requerimientos.items():
            await inventario_service.descontar_stock(
                db,
                id_insumo=id_insumo,
                cantidad=cantidad_requerida,
                id_usuario=id_usuario,
                id_venta=venta.id_venta,
                motivo="salida por venta",
            )

        # ── Step 6: create Pago records and Factura ───────────────────────────
        for pago_data in data.pagos:
            pago = Pago(
                id_venta=venta.id_venta,
                id_metodo_pago=pago_data.id_metodo_pago,
                monto=pago_data.monto,
                url_comprobante=pago_data.url_comprobante,
                # Transfer payments start as pendiente until admin validates comprobante
                estado_validacion="pendiente",
            )
            await venta_repo.create_pago(pago, db)

        # Invoice number is derived from the DB-generated PK — safe under concurrency
        # because no two rows can share the same id_venta sequence value.
        factura = Factura(
            id_venta=venta.id_venta,
            numero=f"FAC-{venta.id_venta:06d}",
            fecha_emision=_now(),
            total=total_pagado,
        )
        await venta_repo.create_factura(factura, db)

        # ── Step 7: close pedido and free the table ───────────────────────────
        if pedido:
            pedido.estado = "pagado"
            if pedido.mesa:
                pedido.mesa.estado = "disponible"

        await db.commit()

        return await venta_repo.get_venta_by_id(venta.id_venta, db)

    except IntegrityError as e:
        await db.rollback()
        # Concurrent duplicate token: the other request's INSERT won the UNIQUE
        # constraint race. Fetch and return that winning sale so both callers
        # receive the same response.
        if data.token_idempotencia and "token_idempotencia" in str(e.orig):
            existing = await venta_repo.get_by_idempotency_token(db, data.token_idempotencia)
            if existing:
                return existing
        raise MajesaError("Conflicto al crear la venta", 409)

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


async def validar_pago(
    id_pago: int,
    data,
    db: AsyncSession,
) -> Pago:
    pago = await venta_repo.get_pago_by_id(id_pago, db)
    if not pago:
        raise MajesaError(f"Pago {id_pago} no encontrado", 404)

    if pago.estado_validacion != "pendiente":
        raise MajesaError("El pago ya fue validado", 409)

    if not pago.metodo_pago.requiere_comprobante:
        raise MajesaError("Este método de pago no requiere validación", 422)

    if data.estado_validacion.value == "pendiente":
        raise MajesaError(
            "El estado de validación debe ser aprobado o rechazado", 422
        )

    pago = await venta_repo.update_pago(
        pago,
        {
            "estado_validacion": data.estado_validacion.value,
            "id_usuario_validacion": data.id_usuario_validacion,
            "fecha_validacion": _now(),
        },
        db,
    )
    await db.commit()
    return pago
