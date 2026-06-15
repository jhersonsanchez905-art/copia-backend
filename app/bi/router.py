"""BI module router — endpoints for the BI dashboard (contrato v3, §4).

Endpoints:
    GET  /api/v1/bi/dashboard/diario      — yesterday's analysis + today's
                                              purchase recommendation
    GET  /api/v1/bi/dashboard/mensual     — current month (partial) + closed
                                              previous month
    GET  /api/v1/bi/meta                  — available date range for the
                                              front's selectors
    GET  /api/v1/bi/diario                — historical day (caso B)
    GET  /api/v1/bi/diario/comparar       — compare two days (caso A)
    GET  /api/v1/bi/diario/rango          — aggregated date range (caso C)
    GET  /api/v1/bi/mensual               — closed month (caso B)
    GET  /api/v1/bi/mensual/comparar      — compare two months (caso A)
    GET  /api/v1/bi/mensual/rango         — aggregated month range (caso C)
    POST /api/v1/bi/procesar-dia          — trigger ETL (CRON_SECRET protected)
    GET  /api/v1/bi/admin/etl/ejecuciones — ETL run history (admin panel)

All GET endpoints require require_rol("administrador") — BI data
(margins, real costs, stock levels) is restricted to admin users.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.bi import service
from app.bi.schemas import (
    ComparacionDiariaSchema,
    ComparacionMensualSchema,
    DashboardDiarioSchema,
    DashboardMensualSchema,
    EjecucionEtlSchema,
    MetaSchema,
    ProcesarDiaRequest,
    ProcesarDiaResponse,
    RangoDiarioSchema,
    RangoMensualSchema,
)
from app.config import settings
from app.database import get_db
from app.dependencies import require_rol

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bi", tags=["BI — Business Intelligence"])

_require_admin = Depends(require_rol("administrador"))


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
    "/dashboard/diario",
    response_model=DashboardDiarioSchema,
    summary="Daily dashboard: yesterday's analysis + today's purchase recommendation.",
    dependencies=[_require_admin],
)
async def dashboard_diario(
    db: AsyncSession = Depends(get_db),
) -> DashboardDiarioSchema:
    """Return yesterday's sales analysis plus today's purchase recommendations.

    Reads from precomputed bi.resumen_diario_* tables (rebuilt nightly
    by the ETL). Includes recomendacion_compra (§4.1).

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        DashboardDiarioSchema with ventas, merma, tops, hourly curve,
        and purchase recommendations.

    Raises:
        HTTPException: 404 if the ETL has never run.
    """
    result = await service.get_dashboard_diario(db, incluir_recomendacion=True)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos disponibles. El ETL no ha procesado ningún día aún.",
        )
    return result


@router.get(
    "/dashboard/mensual",
    response_model=DashboardMensualSchema,
    summary="Monthly dashboard: current month (partial) + closed previous month.",
    dependencies=[_require_admin],
)
async def dashboard_mensual(
    db: AsyncSession = Depends(get_db),
) -> DashboardMensualSchema:
    """Return the current month's analysis plus the previous closed month.

    Reads from precomputed bi.resumen_mensual_* tables. Includes
    mes_anterior (§4.1).

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        DashboardMensualSchema with ranking, ganancia bruta, heatmap,
        signals, warnings, fugas, and the previous month.

    Raises:
        HTTPException: 404 if the current month has never been processed.
    """
    mes_actual = date.today().replace(day=1)
    result = await service.get_dashboard_mensual(
        db, mes_actual, incluir_mes_anterior=True
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos disponibles para el mes actual.",
        )
    return result


@router.get(
    "/meta",
    response_model=MetaSchema,
    summary="Available date range for the front's date-range selectors.",
    dependencies=[_require_admin],
)
async def meta(db: AsyncSession = Depends(get_db)) -> MetaSchema:
    """Return the earliest and most recent dates with processed data.

    Used by the front to bound date-range selectors in Explorar.

    Args:
        db: Async database session injected by FastAPI.

    Returns:
        MetaSchema with historico_desde and ultimo_dia_procesado.
    """
    return await service.get_meta(db)


# ═══════════════════════════════════════════════════════════════════
# Explorar — Diario (§4.2)
# ═══════════════════════════════════════════════════════════════════


@router.get(
    "/diario",
    response_model=DashboardDiarioSchema,
    summary="Historical daily analysis for a specific date (caso B).",
    dependencies=[_require_admin],
)
async def diario_puntual(
    fecha: date, db: AsyncSession = Depends(get_db)
) -> DashboardDiarioSchema:
    """Compute the daily dashboard for a historical date, on the fly.

    Omits recomendacion_compra (not applicable to past dates, §2.3).

    Args:
        fecha: The historical date to analyze (query param).
        db: Async database session injected by FastAPI.

    Returns:
        DashboardDiarioSchema without recomendacion_compra.

    Raises:
        HTTPException: 404 if no ETL data exists for this date.
    """
    result = await service.get_diario_puntual(db, fecha)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay datos procesados para la fecha {fecha}.",
        )
    return result


@router.get(
    "/diario/comparar",
    response_model=ComparacionDiariaSchema,
    summary="Compare two daily dashboards (caso A).",
    dependencies=[_require_admin],
)
async def diario_comparar(
    a: date, b: date, db: AsyncSession = Depends(get_db)
) -> ComparacionDiariaSchema:
    """Compare the daily dashboards of two dates.

    Args:
        a: First date (baseline, query param).
        b: Second date (query param).
        db: Async database session injected by FastAPI.

    Returns:
        ComparacionDiariaSchema with both dashboards + variation.

    Raises:
        HTTPException: 422 if a == b. 404 if either date has no data.
    """
    if a == b:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las fechas a y b deben ser diferentes.",
        )
    result = await service.get_diario_comparar(db, a, b)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Una o ambas fechas no tienen datos procesados.",
        )
    return result


@router.get(
    "/diario/rango",
    response_model=RangoDiarioSchema,
    summary="Aggregated daily dashboard over a date range (caso C).",
    dependencies=[_require_admin],
)
async def diario_rango(
    desde: date, hasta: date, db: AsyncSession = Depends(get_db)
) -> RangoDiarioSchema:
    """Aggregate the daily dashboard over [desde, hasta].

    Args:
        desde: First day of the range (inclusive, query param).
        hasta: Last day of the range (inclusive, query param).
        db: Async database session injected by FastAPI.

    Returns:
        RangoDiarioSchema with dias_incluidos.

    Raises:
        HTTPException: 422 if desde > hasta. 404 if no data in range.
    """
    if desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="desde debe ser menor o igual a hasta.",
        )
    result = await service.get_diario_rango(db, desde, hasta)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos procesados en el rango indicado.",
        )
    return result


# ═══════════════════════════════════════════════════════════════════
# Explorar — Mensual (§4.2)
# ═══════════════════════════════════════════════════════════════════


@router.get(
    "/mensual",
    response_model=DashboardMensualSchema,
    summary="Monthly dashboard for a specific closed month (caso B).",
    dependencies=[_require_admin],
)
async def mensual_puntual(
    mes: date, db: AsyncSession = Depends(get_db)
) -> DashboardMensualSchema:
    """Return the monthly dashboard for a specific month.

    Reads from precomputed bi.resumen_mensual_* tables.
    Does not include mes_anterior (§4.2).

    Args:
        mes: First day of the target month (query param, e.g. 2026-05-01).
        db: Async database session injected by FastAPI.

    Returns:
        DashboardMensualSchema without mes_anterior.

    Raises:
        HTTPException: 404 if that month was never processed.
    """
    result = await service.get_mensual_puntual(db, mes.replace(day=1))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay datos procesados para el mes {mes.strftime('%Y-%m')}.",
        )
    return result


@router.get(
    "/mensual/comparar",
    response_model=ComparacionMensualSchema,
    summary="Compare two monthly dashboards (caso A).",
    dependencies=[_require_admin],
)
async def mensual_comparar(
    a: date, b: date, db: AsyncSession = Depends(get_db)
) -> ComparacionMensualSchema:
    """Compare the monthly dashboards of two months.

    Args:
        a: First month (baseline, query param, e.g. 2026-04-01).
        b: Second month (query param, e.g. 2026-05-01).
        db: Async database session injected by FastAPI.

    Returns:
        ComparacionMensualSchema with both dashboards + variation.

    Raises:
        HTTPException: 422 if a == b. 404 if either month has no data.
    """
    mes_a = a.replace(day=1)
    mes_b = b.replace(day=1)
    if mes_a == mes_b:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los meses a y b deben ser diferentes.",
        )
    result = await service.get_mensual_comparar(db, mes_a, mes_b)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o ambos meses no tienen datos procesados.",
        )
    return result


@router.get(
    "/mensual/rango",
    response_model=RangoMensualSchema,
    summary="Aggregated monthly dashboard over a range of months (caso C).",
    dependencies=[_require_admin],
)
async def mensual_rango(
    desde: date, hasta: date, db: AsyncSession = Depends(get_db)
) -> RangoMensualSchema:
    """Aggregate ranking and ganancia bruta over a range of months.

    senales_precio, warnings_insumo and fugas are returned empty for
    ranges — they don't aggregate meaningfully across months (§4.2,
    per coordination with Darcy 2026-06-15).

    Args:
        desde: First month of the range (query param, e.g. 2026-03-01).
        hasta: Last month of the range (query param, e.g. 2026-06-01).
        db: Async database session injected by FastAPI.

    Returns:
        RangoMensualSchema with meses_incluidos.

    Raises:
        HTTPException: 422 if desde > hasta. 404 if no months have data.
    """
    mes_desde = desde.replace(day=1)
    mes_hasta = hasta.replace(day=1)
    if mes_desde > mes_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="desde debe ser menor o igual a hasta.",
        )
    result = await service.get_mensual_rango(db, mes_desde, mes_hasta)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay datos procesados en el rango de meses indicado.",
        )
    return result


# ═══════════════════════════════════════════════════════════════════
# Operación (§4.4)
# ═══════════════════════════════════════════════════════════════════


@router.post(
    "/procesar-dia",
    response_model=ProcesarDiaResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger the BI ETL pipeline for a given date.",
    dependencies=[Depends(_verify_cron_secret)],
)
async def procesar_dia(
    body: ProcesarDiaRequest,
    db: AsyncSession = Depends(get_db),
) -> ProcesarDiaResponse:
    """Run the full BI ETL pipeline for the specified date.

    Protected by X-Cron-Secret header — not accessible via Clerk auth.
    Intended to be called by an external cron job (02:00 COT / 07:00 UTC)
    and by the 03:00 retrigger safety call.

    Defaults to yesterday in Colombia local time if no date is provided.
    Idempotent: safe to call multiple times for the same date.

    Args:
        body: Optional request body with a fecha field.
        db: Async database session injected by FastAPI.

    Returns:
        ProcesarDiaResponse with ok, id_ejecucion, fecha_procesada,
        and status.
    """
    return await service.procesar_dia(body.fecha, db, origen="cron")


@router.get(
    "/admin/etl/ejecuciones",
    response_model=list[EjecucionEtlSchema],
    summary="Recent ETL run history (admin health panel, §4.4).",
    dependencies=[_require_admin],
)
async def etl_ejecuciones(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
) -> list[EjecucionEtlSchema]:
    """Return the most recent ETL run records.

    Used by the admin panel to monitor the health of the nightly ETL.
    Joins bi.etl_ejecucion with bi.etl_status for human-readable status.

    Args:
        limit: Maximum number of records to return (default 30, max 100).
        db: Async database session injected by FastAPI.

    Returns:
        List of EjecucionEtlSchema ordered by inicio descending.
    """
    if limit > 100:
        limit = 100
    return await service.get_ejecuciones_etl(db, limit)
