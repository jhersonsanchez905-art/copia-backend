"""BI module repository layer for reading summary tables.

All functions perform simple SELECT * queries against bi.resumen_*
tables. No business logic lives here — only data access.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bi.models import (
    ResumenHeatmapHoraDia,
    ResumenRankingProducto,
    ResumenRecomendacionCompra,
    ResumenSenalPrecio,
    ResumenTesteoProducto,
    ResumenWarningInsumo,
)


async def get_ranking_productos(db: AsyncSession) -> list[ResumenRankingProducto]:
    """Fetch all rows from bi.resumen_ranking_producto.

    Args:
        db: Async database session.

    Returns:
        List of ResumenRankingProducto ORM instances.
    """
    result = await db.execute(select(ResumenRankingProducto))
    return list(result.scalars().all())


async def get_heatmap(db: AsyncSession) -> list[ResumenHeatmapHoraDia]:
    """Fetch all rows from bi.resumen_heatmap_hora_dia.

    Args:
        db: Async database session.

    Returns:
        List of ResumenHeatmapHoraDia ORM instances (max 168 rows).
    """
    result = await db.execute(select(ResumenHeatmapHoraDia))
    return list(result.scalars().all())


async def get_recomendacion_compra(
    db: AsyncSession,
) -> list[ResumenRecomendacionCompra]:
    """Fetch all rows from bi.resumen_recomendacion_compra.

    Args:
        db: Async database session.

    Returns:
        List of ResumenRecomendacionCompra ORM instances.
    """
    result = await db.execute(select(ResumenRecomendacionCompra))
    return list(result.scalars().all())


async def get_senales_precio(db: AsyncSession) -> list[ResumenSenalPrecio]:
    """Fetch all rows from bi.resumen_senal_precio.

    Args:
        db: Async database session.

    Returns:
        List of ResumenSenalPrecio ORM instances.
    """
    result = await db.execute(select(ResumenSenalPrecio))
    return list(result.scalars().all())


async def get_testeo_productos(db: AsyncSession) -> list[ResumenTesteoProducto]:
    """Fetch all rows from bi.resumen_testeo_producto.

    Args:
        db: Async database session.

    Returns:
        List of ResumenTesteoProducto ORM instances (daily series).
    """
    result = await db.execute(select(ResumenTesteoProducto))
    return list(result.scalars().all())


async def get_warnings_insumo(db: AsyncSession) -> list[ResumenWarningInsumo]:
    """Fetch all rows from bi.resumen_warning_insumo.

    Args:
        db: Async database session.

    Returns:
        List of ResumenWarningInsumo ORM instances.
    """
    result = await db.execute(select(ResumenWarningInsumo))
    return list(result.scalars().all())
