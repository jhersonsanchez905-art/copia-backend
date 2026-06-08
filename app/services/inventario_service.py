"""
inventario_service.py
Async business logic for MovimientoInventario and Alerta (semaforo).
AjusteInventario has its own service (ajuste_inventario_service.py).
Stock updates are triggered by venta registration and approved adjustments.
"""
import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import InsumoInsuficienteError
from app.models.inventario import Alerta, MovimientoInventario
from app.models.insumo import Insumo
from app.models.stock import Stock
from app.repositories import inventario_repo, stock_repo


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _calcular_semaforo(cantidad: Decimal, insumo: Insumo) -> str:
    if cantidad <= insumo.umbral_minimo:
        return "rojo"
    if cantidad <= insumo.stock_minimo:
        return "amarillo"
    return "verde"


async def descontar_stock(
    db: AsyncSession,
    id_insumo: int,
    cantidad: Decimal,
    id_usuario: int,
    id_venta: int | None = None,
    id_orden_compra: int | None = None,
    motivo: str = "salida por venta",
) -> Stock:
    """
    Deducts `cantidad` from the stock of `id_insumo`.
    Creates a MovimientoInventario record.
    Updates Stock.semaforo and creates Alerta if threshold is breached.
    Must be called within an open DB transaction.
    """
    from app.exceptions import InsumoInsuficienteError

    stock = await stock_repo.get_stock_by_insumo(db, id_insumo)
    if stock is None:
        raise InsumoInsuficienteError(f"No existe registro de stock para insumo {id_insumo}", 422)

    cantidad_anterior = stock.cantidad
    cantidad_nueva = cantidad_anterior - cantidad

    if cantidad_nueva < 0:
        raise InsumoInsuficienteError(
            f"Stock insuficiente para insumo {id_insumo}: disponible={cantidad_anterior}, requerido={cantidad}",
            422,
        )

    insumo = stock.insumo
    nuevo_semaforo = _calcular_semaforo(cantidad_nueva, insumo)

    await stock_repo.update_stock(db, stock, cantidad_nueva, nuevo_semaforo)

    movimiento = MovimientoInventario(
        id_insumo=id_insumo,
        tipo="salida",
        cantidad=cantidad,
        cantidad_anterior=cantidad_anterior,
        cantidad_nueva=cantidad_nueva,
        motivo=motivo,
        id_venta=id_venta,
        id_orden_compra=id_orden_compra,
        id_usuario=id_usuario,
        fecha=_now(),
    )
    await inventario_repo.create_movimiento(db, movimiento)

    await _evaluar_semaforo(db, id_insumo, cantidad_nueva, insumo)

    return stock


async def ingresar_stock(
    db: AsyncSession,
    id_insumo: int,
    cantidad: Decimal,
    id_usuario: int,
    id_orden_compra: int | None = None,
    motivo: str = "entrada por recepción",
) -> Stock:
    """
    Adds `cantidad` to the stock of `id_insumo`.
    Creates a MovimientoInventario record.
    Resolves active Alerta if stock is now above threshold.
    """
    stock = await stock_repo.get_stock_by_insumo(db, id_insumo)
    if stock is None:
        stock = Stock(id_insumo=id_insumo, cantidad=Decimal("0"), semaforo="rojo")
        await stock_repo.create_stock(db, stock)

    cantidad_anterior = stock.cantidad
    cantidad_nueva = cantidad_anterior + cantidad
    insumo = stock.insumo
    nuevo_semaforo = _calcular_semaforo(cantidad_nueva, insumo)

    await stock_repo.update_stock(db, stock, cantidad_nueva, nuevo_semaforo)

    movimiento = MovimientoInventario(
        id_insumo=id_insumo,
        tipo="entrada",
        cantidad=cantidad,
        cantidad_anterior=cantidad_anterior,
        cantidad_nueva=cantidad_nueva,
        motivo=motivo,
        id_orden_compra=id_orden_compra,
        id_usuario=id_usuario,
        fecha=_now(),
    )
    await inventario_repo.create_movimiento(db, movimiento)

    await _evaluar_semaforo(db, id_insumo, cantidad_nueva, insumo)

    return stock


async def _evaluar_semaforo(
    db: AsyncSession,
    id_insumo: int,
    cantidad_nueva: Decimal,
    insumo: Insumo,
) -> None:
    """Creates or resolves Alerta based on current stock vs thresholds."""
    alerta_existente = await inventario_repo.get_alerta_activa_by_insumo(db, id_insumo)

    if cantidad_nueva <= insumo.stock_minimo:
        semaforo = _calcular_semaforo(cantidad_nueva, insumo)
        tipo = "stock_critico" if semaforo == "rojo" else "stock_bajo"
        if not alerta_existente:
            alerta = Alerta(
                id_insumo=id_insumo,
                tipo=tipo,
                estado="activa",
                semaforo=semaforo,
                cantidad_a_pedir=insumo.cantidad_a_pedir,
                fecha_creacion=_now(),
            )
            await inventario_repo.create_alerta(db, alerta)
        else:
            alerta_existente.semaforo = semaforo
            alerta_existente.tipo = tipo
    else:
        if alerta_existente:
            await inventario_repo.resolver_alerta(db, id_insumo)


async def get_alertas_activas(db: AsyncSession) -> list[Alerta]:
    return await inventario_repo.get_alertas_activas(db)


async def get_movimientos_by_insumo(
    db: AsyncSession, id_insumo: int
) -> list[MovimientoInventario]:
    return await inventario_repo.get_movimientos_by_insumo(db, id_insumo)
