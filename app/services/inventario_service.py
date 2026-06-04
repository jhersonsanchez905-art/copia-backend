"""
app/services/inventario_service.py

Business logic for inventory module.
Handles manual adjustments, approvals, alerts and traffic light system.

Author: Suley Suarez
Issue: #16
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.schemas.inventario_schema import (
    AjusteInventarioRequest,
    AprobacionAjusteRequest,
    EstadoAjusteEnum
)
from app.repositories import inventario_repo
from app.models.inventario import MovimientoInventario, Alerta
from app.exceptions import MajesaError, PermisoDenegadoError


async def registrar_ajuste_manual(
    data: AjusteInventarioRequest,
    id_usuario: int,
    db: AsyncSession
) -> MovimientoInventario:
    """
    Register a manual inventory adjustment with status PENDIENTE.
    Does NOT modify stock until approved by an admin.
    Sends email notification to admin via Resend (TODO).

    Raises:
        MajesaError: If the supply item does not exist.
    """
    async with db.begin():
        insumo = await inventario_repo.get_insumo_by_id(data.id_insumo, db)
        if not insumo:
            raise MajesaError(f"Insumo {data.id_insumo} no encontrado", 404)

        movimiento = MovimientoInventario(
            id_insumo=data.id_insumo,
            id_usuario=id_usuario,
            tipo="ajuste",
            cantidad=data.cantidad,
            motivo=data.motivo,
            observacion=data.observacion,
            afecta_stock=False,
            cantidad_anterior=insumo.stock_actual,
            cantidad_nueva=insumo.stock_actual + data.cantidad,
            estado="pendiente",
            fecha=datetime.utcnow()
        )
        movimiento = await inventario_repo.create_movimiento(movimiento, db)

        # TODO: enviar correo al admin via Resend

        return movimiento


async def aprobar_ajuste(
    id_movimiento: int,
    data: AprobacionAjusteRequest,
    id_aprobador: int,
    db: AsyncSession
) -> MovimientoInventario:
    """
    Approve or reject a pending manual inventory adjustment.
    If approved, updates the stock and checks alert thresholds.
    Only admin role can call this endpoint.

    Raises:
        MajesaError: If the movement does not exist or is not pending.
        PermisoDenegadoError: If the user is not an admin.
    """
    async with db.begin():
        movimiento = await inventario_repo.get_movimiento_by_id(id_movimiento, db)
        if not movimiento:
            raise MajesaError(f"Movimiento {id_movimiento} no encontrado", 404)
        if movimiento.estado != "pendiente":
            raise MajesaError("Este ajuste ya fue procesado", 409)

        await inventario_repo.update_movimiento_estado(
            id_movimiento, data.estado.value, id_aprobador, db
        )

        if data.estado == EstadoAjusteEnum.aprobado:
            insumo = await inventario_repo.get_insumo_by_id(movimiento.id_insumo, db)
            nuevo_stock = insumo.stock_actual + movimiento.cantidad
            await inventario_repo.update_stock(movimiento.id_insumo, nuevo_stock, db)
            await verificar_semaforo(movimiento.id_insumo, nuevo_stock, db)

        return movimiento


async def verificar_semaforo(
    id_insumo: int,
    stock_actual: float,
    db: AsyncSession
) -> None:
    """
    Check if the current stock triggers an alert.
    Creates an active alert if stock is below minimum threshold.
    Resolves existing alert if stock is back above minimum.

    Called automatically after every stock deduction or approved adjustment.
    """
    insumo = await inventario_repo.get_insumo_by_id(id_insumo, db)
    if not insumo:
        return

    alerta_existente = await inventario_repo.get_alerta_activa_by_insumo(id_insumo, db)

    if stock_actual <= insumo.stock_minimo:
        if not alerta_existente:
            semaforo = "rojo" if stock_actual == 0 else "amarillo"
            alerta = Alerta(
                id_insumo=id_insumo,
                estado="activa",
                semaforo=semaforo,
                cantidad_a_pedir=insumo.cantidad_a_pedir,
                fecha_creacion=datetime.utcnow()
            )
            await inventario_repo.create_alerta(alerta, db)
            # TODO: enviar correo al admin via Resend
    else:
        if alerta_existente:
            await inventario_repo.resolver_alerta(id_insumo, db)


async def get_alertas_activas(db: AsyncSession) -> list[Alerta]:
    """Retrieve all active inventory alerts."""
    return await inventario_repo.get_alertas_activas(db)
