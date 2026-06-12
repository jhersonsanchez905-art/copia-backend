"""BI module service layer.

Thin orchestration layer between the router and the repository/ETL.
Handles date defaulting for procesar_dia and delegates all data
access to repo.py and etl_service.py.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.bi import etl_service, repo
from app.bi.schemas import (
    HeatmapHoraDiaSchema,
    ProcesarDiaResponse,
    RankingProductoSchema,
    RecomendacionCompraSchema,
    SenalPrecioSchema,
    TesteoProductoSchema,
    WarningInsumoSchema,
)

BOGOTA_TZ = ZoneInfo("America/Bogota")


def _fecha_caida() -> date:
    """Return yesterday's date in Colombia local time.

    Returns:
        Yesterday as a date object in America/Bogota timezone.
    """
    from datetime import datetime

    return (datetime.now(tz=BOGOTA_TZ) - timedelta(days=1)).date()


async def get_ranking_productos(db: AsyncSession) -> list[RankingProductoSchema]:
    """Return product ranking for the last 30 days.

    Args:
        db: Async database session.

    Returns:
        List of RankingProductoSchema instances.
    """
    rows = await repo.get_ranking_productos(db)
    return [RankingProductoSchema.model_validate(r) for r in rows]


async def get_heatmap(db: AsyncSession) -> list[HeatmapHoraDiaSchema]:
    """Return hourly sales heatmap averages for the last 90 days.

    Args:
        db: Async database session.

    Returns:
        List of HeatmapHoraDiaSchema instances (max 168 rows).
    """
    rows = await repo.get_heatmap(db)
    return [HeatmapHoraDiaSchema.model_validate(r) for r in rows]


async def get_recomendacion_compra(
    db: AsyncSession,
) -> list[RecomendacionCompraSchema]:
    """Return purchase recommendations for all active ingredients.

    Args:
        db: Async database session.

    Returns:
        List of RecomendacionCompraSchema instances.
    """
    rows = await repo.get_recomendacion_compra(db)
    return [RecomendacionCompraSchema.model_validate(r) for r in rows]


async def get_senales_precio(db: AsyncSession) -> list[SenalPrecioSchema]:
    """Return price signal flags for products with low margin and high volume.

    Args:
        db: Async database session.

    Returns:
        List of SenalPrecioSchema instances.
    """
    rows = await repo.get_senales_precio(db)
    return [SenalPrecioSchema.model_validate(r) for r in rows]


async def get_testeo_productos(db: AsyncSession) -> list[TesteoProductoSchema]:
    """Return daily performance series for recently launched products.

    Args:
        db: Async database session.

    Returns:
        List of TesteoProductoSchema instances.
    """
    rows = await repo.get_testeo_productos(db)
    return [TesteoProductoSchema.model_validate(r) for r in rows]


async def get_warnings_insumo(db: AsyncSession) -> list[WarningInsumoSchema]:
    """Return shared ingredient warnings for low-margin products.

    Args:
        db: Async database session.

    Returns:
        List of WarningInsumoSchema instances.
    """
    rows = await repo.get_warnings_insumo(db)
    return [WarningInsumoSchema.model_validate(r) for r in rows]


async def procesar_dia(
    fecha: date | None,
    db: AsyncSession,
) -> ProcesarDiaResponse:
    """Run the BI ETL pipeline for a given date.

    Defaults to yesterday in Colombia local time if no date is provided.

    Args:
        fecha: The business day to process. Defaults to yesterday (COT).
        db: Async database session.

    Returns:
        ProcesarDiaResponse with ok flag, processed date and duration.
    """
    import time

    fecha_a_procesar = fecha or _fecha_caida()
    inicio = time.perf_counter()

    await etl_service.procesar_dia(fecha_a_procesar, db)

    duracion_ms = int((time.perf_counter() - inicio) * 1000)
    return ProcesarDiaResponse(
        ok=True,
        fecha_procesada=fecha_a_procesar,
        duracion_ms=duracion_ms,
    )
