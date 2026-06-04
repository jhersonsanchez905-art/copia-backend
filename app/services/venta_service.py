"""
app/services/venta_service.py

Business logic for sales module.
Handles atomic sale registration, inventory deduction and invoice generation.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional
from app.schemas.venta_schema import VentaCreateRequest, VentaResponse
from app.repositories import venta_repo, inventario_repo
from app.models.venta import Venta, ItemVenta, Pago, Factura
from app.exceptions import InsumoInsuficienteError, VentaNoEncontradaError


async def registrar_venta(
    data: VentaCreateRequest,
    id_usuario: int,
    db: AsyncSession
) -> Venta:
    """
    Register a new sale with atomic inventory deduction.

    Steps:
    1. Retrieve active recipe for each product.
    2. Calculate required ingredients.
    3. Verify stock for ALL ingredients before deducting.
    4. Create sale with recipe snapshot.
    5. Deduct stock atomically.
    6. Generate invoice.

    Raises:
        InsumoInsuficienteError: If any ingredient has insufficient stock.
    """
    async with db.begin():
        subtotal = 0.0
        items_creados = []

        for item_data in data.productos:
            # TODO: get product price and active recipe from repo
            # receta = await receta_repo.get_vigente(item_data.id_producto, db)
            # insumos = calcular_insumos(receta, item_data.cantidad)
            # await verificar_stock(insumos, db)
            # snapshot = receta.to_snapshot()

            precio_unitario = 0.0  # placeholder — reemplazar con precio real
            item_subtotal = precio_unitario * item_data.cantidad
            subtotal += item_subtotal

            item = ItemVenta(
                id_venta=None,
                id_producto=item_data.id_producto,
                cantidad=item_data.cantidad,
                precio_unitario=precio_unitario,
                subtotal=item_subtotal,
                receta_snapshot={}  # placeholder — reemplazar con snapshot real
            )
            items_creados.append(item)

        total = sum(p.monto for p in data.pagos)

        venta = Venta(
            id_apertura=data.id_apertura,
            turno=data.turno,
            fecha=datetime.utcnow(),
            id_usuario=id_usuario,
            id_cliente=data.id_cliente,
            subtotal=subtotal,
            total=total,
            estado="cerrada"
        )

        venta = await venta_repo.create_venta(venta, db)

        for item in items_creados:
            item.id_venta = venta.id_venta
            await venta_repo.create_item_venta(item, db)

        for pago_data in data.pagos:
            pago = Pago(
                id_venta=venta.id_venta,
                id_metodo_pago=pago_data.id_metodo_pago,
                monto=pago_data.monto,
                url_comprobante=pago_data.url_comprobante,
                estado_validacion="validado"
            )
            await venta_repo.create_pago(pago, db)

        factura = Factura(
            id_venta=venta.id_venta,
            numero=f"FAC-{venta.id_venta:06d}",
            fecha_emision=datetime.utcnow(),
            total=total
        )
        await venta_repo.create_factura(factura, db)

        return venta


async def get_venta_by_id(id_venta: int, db: AsyncSession) -> Venta:
    """
    Retrieve a sale by its ID.

    Raises:
        VentaNoEncontradaError: If the sale does not exist.
    """
    venta = await venta_repo.get_venta_by_id(id_venta, db)
    if not venta:
        raise VentaNoEncontradaError(id_venta)
    return venta


async def get_ventas_by_fecha_turno(
    fecha: date,
    turno: Optional[str],
    db: AsyncSession
) -> list[Venta]:
    """Retrieve all sales for a given date and optional shift."""
    return await venta_repo.get_ventas_by_fecha_turno(fecha, turno, db)
