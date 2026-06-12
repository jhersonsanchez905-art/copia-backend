"""
alerta_perecible_service.py
Async service for AlertaPerecible.
Includes manual evaluation endpoint for administrators.
fecha_ingreso is taken from the last MovimientoInventario with tipo='entrada'.
"""
import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.alerta_perecible import AlertaPerecible
from app.repositories import alerta_perecible_repo


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def get_alerta_perecible(db: AsyncSession, id_alerta: int) -> AlertaPerecible:
    alerta = await alerta_perecible_repo.get_alerta_perecible_by_id(db, id_alerta)
    if not alerta:
        raise MajesaError(f"AlertaPerecible {id_alerta} no encontrada", 404)
    return alerta


async def get_alertas_perecibles(
    db: AsyncSession,
    estado: str | None = None,
    id_insumo: int | None = None,
) -> list[AlertaPerecible]:
    return await alerta_perecible_repo.get_alertas_perecibles(
        db, estado=estado, id_insumo=id_insumo
    )


async def evaluar_perecibles(
    db: AsyncSession,
    dias_alerta: int = 3,
) -> dict:
    """
    Manually evaluate perishable items in stock.
    Creates alerts for items that have been in inventory for more than dias_alerta days.
    fecha_ingreso is taken from the last MovimientoInventario with tipo='entrada'.
    Only creates alert if there is no active alert for that insumo/stock already.
    Returns a summary of alerts created and skipped.
    """
    stocks = await alerta_perecible_repo.get_stocks_activos(db)
    hoy = _now().date()
    creadas = 0
    omitidas = 0
    alertas_creadas = []

    for stock in stocks:
        movimiento = await alerta_perecible_repo.get_ultimo_movimiento_entrada(
            db, stock.id_insumo
        )
        if not movimiento:
            omitidas += 1
            continue

        fecha_ingreso = movimiento.fecha.date()
        dias_en_inventario = (hoy - fecha_ingreso).days

        if dias_en_inventario < dias_alerta:
            omitidas += 1
            continue

        alerta_existente = await alerta_perecible_repo.get_alerta_perecible_activa(
            db, stock.id_insumo, stock.id_stock
        )
        if alerta_existente:
            omitidas += 1
            continue

        alerta = AlertaPerecible(
            id_insumo=stock.id_insumo,
            id_stock=stock.id_stock,
            fecha_ingreso=fecha_ingreso,
            dias_en_inventario=dias_en_inventario,
            estado="activa",
            accion_sugerida=f"Insumo lleva {dias_en_inventario} días en inventario. Revisar estado.",
            fecha_creacion=_now(),
        )
        alerta = await alerta_perecible_repo.create_alerta_perecible(db, alerta)
        alertas_creadas.append(alerta)
        creadas += 1

    await db.commit()
    return {
        "alertas_creadas": creadas,
        "omitidas": omitidas,
        "detalle": alertas_creadas,
    }