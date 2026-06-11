"""BI module router — 7 endpoints for the BI dashboard.

Endpoints:
    GET  /api/v1/bi/ranking-productos     — product ranking (last 30 days)
    GET  /api/v1/bi/heatmap               — hourly sales heatmap (last 90 days)
    GET  /api/v1/bi/recomendacion-compra  — purchase recommendations
    GET  /api/v1/bi/senales-precio        — price signal flags
    GET  /api/v1/bi/testeo-productos      — new product performance series
    GET  /api/v1/bi/warnings-insumo       — shared ingredient warnings
    POST /api/v1/bi/procesar-dia          — trigger ETL (CRON_SECRET protected)

All GET endpoints read from bi.resumen_* tables (pre-computed by ETL).
No heavy computation happens at request time.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.bi import service
from app.bi.schemas import (
    HeatmapHoraDiaSchema,
    ProcesarDiaRequest,
    ProcesarDiaResponse,
    RankingProductoSchema,
    RecomendacionCompraSchema,
    SenalPrecioSchema,
    TesteoProductoSchema,
    WarningInsumoSchema,
)
from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bi", tags=["BI — Business Intelligence"])


def _verify_cron_secret(x_cron_secret: str = Header(...)) -> None:
    """Validate the CRON_SECRET header for the ETL endpoint.

    Args:
        x_cron_secret: Value of the X-Cron-Secret request header.

    Raises:
        HTTPException: 401 if the secret does not match.
    """
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing CRON_SECRET.",
        )


@router.get(
    "/ranking-productos",
    response_model=list[RankingProductoSchema],
    summary="Product ranking by margin and volume (last 30 days).",
)
async def ranking_productos(
    db: AsyncSession = Depends(get_db),
) -> list[RankingProductoSchema]:
    """Return all products ranked by margin and sales volume.

    Data is pre-computed by the nightly ETL from the last 30 days
    of sales. Response is read directly from bi.resumen_ranking_producto.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of products with units sold, total margin and margin percentage.
    """
    return await service.get_ranking_productos(db)


@router.get(
    "/heatmap",
    response_model=list[HeatmapHoraDiaSchema],
    summary="Hourly sales heatmap averaged over the last 90 days.",
)
async def heatmap(
    db: AsyncSession = Depends(get_db),
) -> list[HeatmapHoraDiaSchema]:
    """Return average sales per hour and day of week.

    Maximum 168 rows (7 days × 24 hours). Hours are in Colombia
    local time (America/Bogota, UTC-5, no DST).

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of hourly averages grouped by day of week and hour.
    """
    return await service.get_heatmap(db)


@router.get(
    "/recomendacion-compra",
    response_model=list[RecomendacionCompraSchema],
    summary="Purchase recommendations for active ingredients.",
)
async def recomendacion_compra(
    db: AsyncSession = Depends(get_db),
) -> list[RecomendacionCompraSchema]:
    """Return purchase recommendations based on consumption rate and stock.

    Formula: punto_pedido = daily_rate * dias_anticipacion + stock_minimo.
    Order quantity covers 7 days with a 20% buffer minus current stock.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of ingredients with stock, consumption rate and order quantity.
    """
    return await service.get_recomendacion_compra(db)


@router.get(
    "/senales-precio",
    response_model=list[SenalPrecioSchema],
    summary="Price signals: low margin products with high sales volume.",
)
async def senales_precio(
    db: AsyncSession = Depends(get_db),
) -> list[SenalPrecioSchema]:
    """Return products flagged for price review.

    A product is flagged when its margin is at or below the 25th
    percentile AND its volume is at or above the 50th percentile
    across all products in the last 30 days.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of products with margin percentage and revisar_precio flag.
    """
    return await service.get_senales_precio(db)


@router.get(
    "/testeo-productos",
    response_model=list[TesteoProductoSchema],
    summary="Daily performance series for products launched in the last 60 days.",
)
async def testeo_productos(
    db: AsyncSession = Depends(get_db),
) -> list[TesteoProductoSchema]:
    """Return daily sales and margin for recently launched products.

    Only includes products where pos.producto.fecha_lanzamiento
    is within the last 60 days. Returns one row per product per day.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of daily performance records for new products.
    """
    return await service.get_testeo_productos(db)


@router.get(
    "/warnings-insumo",
    response_model=list[WarningInsumoSchema],
    summary="Shared ingredient warnings for low-margin products.",
)
async def warnings_insumo(
    db: AsyncSession = Depends(get_db),
) -> list[WarningInsumoSchema]:
    """Return ingredient sharing warnings for products with low margins.

    An alert fires when a product has margin at or below P25 AND
    consumes 30% or more of an ingredient shared by 2+ products.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        List of product-ingredient pairs with alert flag.
    """
    return await service.get_warnings_insumo(db)


@router.post(
    "/procesar-dia",
    response_model=ProcesarDiaResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger the BI ETL pipeline for a given date.",
    dependencies=[Depends(_verify_cron_secret)],
)
async def procesar_dia(
    body: ProcesarDiaRequest = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ProcesarDiaResponse:
    """Run the full BI ETL pipeline for the specified date.

    Protected by X-Cron-Secret header. Intended to be called by
    an external cron job at 07:00 UTC (02:00 am Colombia).

    Defaults to yesterday in Colombia local time if no date is provided.
    Safe to call multiple times for the same date (idempotent upserts).

    Args:
        body: Optional request body with a fecha field.
        db: Async database session injected by FastAPI.

    Returns:
        ProcesarDiaResponse with ok flag, processed date and duration in ms.
    """
    return await service.procesar_dia(body.fecha, db)
