"""BI module repository layer for reading summary tables.

All functions perform read-only queries against bi.resumen_* and
bi.etl_* tables. No business logic lives here — only data access.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bi.models import (
    EtlEjecucion,
    EtlStatus,
    ResumenDiarioHoras,
    ResumenDiarioTopInsumo,
    ResumenDiarioTopProducto,
    ResumenDiarioVentas,
    ResumenMensualHeatmap,
    ResumenMensualInsumo,
    ResumenMensualMeta,
    ResumenMensualRanking,
    ResumenMensualSenalPrecio,
    ResumenMensualWarningInsumo,
    ResumenRecomendacionCompra,
)

# ═══════════════════════════════════════════════════════════════════
# Diarios — singleton snapshot of "yesterday" (no fecha in PK)
# ═══════════════════════════════════════════════════════════════════


async def get_resumen_diario_ventas(db: AsyncSession) -> ResumenDiarioVentas | None:
    """Fetch the single row from bi.resumen_diario_ventas.

    Args:
        db: Async database session.

    Returns:
        The ResumenDiarioVentas row, or None if the ETL has never run.
    """
    result = await db.execute(select(ResumenDiarioVentas))
    return result.scalars().first()


async def get_top_productos_diario(db: AsyncSession) -> list[ResumenDiarioTopProducto]:
    """Fetch the daily product podium (positions 1-3), ordered.

    Args:
        db: Async database session.

    Returns:
        List of ResumenDiarioTopProducto, ordered by posicion ascending.
    """
    result = await db.execute(
        select(ResumenDiarioTopProducto).order_by(ResumenDiarioTopProducto.posicion)
    )
    return list(result.scalars().all())


async def get_top_insumos_diario(db: AsyncSession) -> list[ResumenDiarioTopInsumo]:
    """Fetch the daily ingredient top-5, ordered by valor_consumo desc.

    Args:
        db: Async database session.

    Returns:
        List of ResumenDiarioTopInsumo, ordered by posicion ascending.
    """
    result = await db.execute(
        select(ResumenDiarioTopInsumo).order_by(ResumenDiarioTopInsumo.posicion)
    )
    return list(result.scalars().all())


async def get_horas_diario(db: AsyncSession) -> list[ResumenDiarioHoras]:
    """Fetch the 24-hour sales curve for the daily dashboard.

    Args:
        db: Async database session.

    Returns:
        List of ResumenDiarioHoras (24 rows, hours 0-23), ordered.
    """
    result = await db.execute(
        select(ResumenDiarioHoras).order_by(ResumenDiarioHoras.hora)
    )
    return list(result.scalars().all())


async def get_recomendacion_compra(
    db: AsyncSession,
) -> list[ResumenRecomendacionCompra]:
    """Fetch all purchase recommendations (only meaningful for "today").

    Args:
        db: Async database session.

    Returns:
        List of ResumenRecomendacionCompra, all ingredients.
    """
    result = await db.execute(select(ResumenRecomendacionCompra))
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════
# Mensuales — historical, keyed by mes (DATE, day 1 of month)
# ═══════════════════════════════════════════════════════════════════


async def get_resumen_mensual_meta(
    db: AsyncSession, mes: date
) -> ResumenMensualMeta | None:
    """Fetch metadata for a given month (parcial flag, dias_con_datos).

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        The ResumenMensualMeta row, or None if that month has no data.
    """
    result = await db.execute(
        select(ResumenMensualMeta).where(ResumenMensualMeta.mes == mes)
    )
    return result.scalars().first()


async def get_ranking_mensual(
    db: AsyncSession, mes: date
) -> list[ResumenMensualRanking]:
    """Fetch product ranking (units + ganancia_bruta) for a given month.

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        List of ResumenMensualRanking rows for that month.
    """
    result = await db.execute(
        select(ResumenMensualRanking).where(ResumenMensualRanking.mes == mes)
    )
    return list(result.scalars().all())


async def get_heatmap_mensual(
    db: AsyncSession, mes: date
) -> list[ResumenMensualHeatmap]:
    """Fetch the day-of-week x hour heatmap for a given month.

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        List of ResumenMensualHeatmap rows for that month.
    """
    result = await db.execute(
        select(ResumenMensualHeatmap).where(ResumenMensualHeatmap.mes == mes)
    )
    return list(result.scalars().all())


async def get_senales_precio_mensual(
    db: AsyncSession, mes: date
) -> list[ResumenMensualSenalPrecio]:
    """Fetch price signal flags for a given month.

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        List of ResumenMensualSenalPrecio rows for that month.
    """
    result = await db.execute(
        select(ResumenMensualSenalPrecio).where(ResumenMensualSenalPrecio.mes == mes)
    )
    return list(result.scalars().all())


async def get_warnings_insumo_mensual(
    db: AsyncSession, mes: date
) -> list[ResumenMensualWarningInsumo]:
    """Fetch shared-ingredient warning flags for a given month.

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        List of ResumenMensualWarningInsumo rows for that month.
    """
    result = await db.execute(
        select(ResumenMensualWarningInsumo).where(
            ResumenMensualWarningInsumo.mes == mes
        )
    )
    return list(result.scalars().all())


async def get_resumen_insumo_mensual(
    db: AsyncSession, mes: date
) -> list[ResumenMensualInsumo]:
    """Fetch ingredient consumption + fugas data for a given month.

    Used to derive both top_insumo and fugas in the monthly dashboard.

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        List of ResumenMensualInsumo rows for that month.
    """
    result = await db.execute(
        select(ResumenMensualInsumo).where(ResumenMensualInsumo.mes == mes)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════
# Auditoría ETL — bi.etl_ejecucion (para /bi/meta y /bi/admin/etl/*)
# ═══════════════════════════════════════════════════════════════════


async def get_ultima_ejecucion_exitosa(db: AsyncSession) -> EtlEjecucion | None:
    """Fetch the most recent successful ETL run.

    Used by GET /bi/meta to compute ultimo_dia_procesado.

    Args:
        db: Async database session.

    Returns:
        The most recent EtlEjecucion with status='exitoso', or None.
    """
    result = await db.execute(
        select(EtlEjecucion)
        .join(EtlStatus, EtlEjecucion.id_status == EtlStatus.id_status)
        .where(EtlStatus.nombre == "exitoso")
        .order_by(EtlEjecucion.fecha_procesada.desc())
        .limit(1)
    )
    return result.scalars().first()


async def get_primera_fecha_procesada(db: AsyncSession) -> date | None:
    """Fetch the earliest fecha_procesada with a successful ETL run.

    Used by GET /bi/meta to compute historico_desde.

    Args:
        db: Async database session.

    Returns:
        The earliest date with a successful run, or None if no
        successful run exists yet.
    """
    result = await db.execute(
        select(EtlEjecucion.fecha_procesada)
        .join(EtlStatus, EtlEjecucion.id_status == EtlStatus.id_status)
        .where(EtlStatus.nombre == "exitoso")
        .order_by(EtlEjecucion.fecha_procesada.asc())
        .limit(1)
    )
    return result.scalars().first()


async def get_ejecuciones_etl(db: AsyncSession, limit: int = 30) -> list[dict]:
    """Fetch recent ETL run history for the admin health panel.

    Joins against bi.etl_status to return the human-readable status
    name (matches EjecucionEtlSchema.status: str).

    Args:
        db: Async database session.
        limit: Maximum number of rows to return (default 30, per §4.4).

    Returns:
        List of dicts with id_ejecucion, fecha_procesada, origen,
        intento, status (name), inicio, fin.
    """
    result = await db.execute(
        select(
            EtlEjecucion.id_ejecucion,
            EtlEjecucion.fecha_procesada,
            EtlEjecucion.origen,
            EtlEjecucion.intento,
            EtlStatus.nombre.label("status"),
            EtlEjecucion.inicio,
            EtlEjecucion.fin,
        )
        .join(EtlStatus, EtlEjecucion.id_status == EtlStatus.id_status)
        .order_by(EtlEjecucion.inicio.desc())
        .limit(limit)
    )
    return [dict(row._mapping) for row in result.all()]
