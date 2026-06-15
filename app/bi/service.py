"""BI module service layer.

Thin orchestration layer between the router and the repository/ETL.
Assembles repo.py rows into the compound schemas of the v3 contract
(documento_canonico §4) and handles date defaulting for procesar_dia.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.bi import etl_service, queries, repo
from app.bi.schemas import (
    DashboardDiarioSchema,
    DashboardMensualSchema,
    EjecucionEtlSchema,
    FugaInsumoSchema,
    GananciaBrutaSchema,
    MermaSchema,
    MetaSchema,
    PicoHoraSchema,
    ProcesarDiaResponse,
    RankingCantidadSchema,
    ReferenciaVentasSchema,
    SenalPrecioSchema,
    TopInsumoMesSchema,
    TopInsumoSchema,
    TopProductoMesSchema,
    TopProductoSchema,
    VariacionVentasSchema,
    VentaHoraSchema,
    VentasDiariasSchema,
    WarningInsumoSchema,
)

BOGOTA_TZ = ZoneInfo("America/Bogota")


def _fecha_ayer() -> date:
    """Return yesterday's date in Colombia local time.

    Returns:
        Yesterday as a date object in America/Bogota timezone.
    """
    return (datetime.now(tz=BOGOTA_TZ) - timedelta(days=1)).date()


async def get_dashboard_diario(
    db: AsyncSession, incluir_recomendacion: bool = True
) -> DashboardDiarioSchema | None:
    """Assemble the daily dashboard (GET /bi/dashboard/diario, §4.1).

    Combines 5 daily summary tables into a single nested response.

    Args:
        db: Async database session.
        incluir_recomendacion: If False, omits recomendacion_compra
            (used by GET /bi/diario — historical days, per §4.2).

    Returns:
        DashboardDiarioSchema, or None if the ETL has never run
        (bi.resumen_diario_ventas is empty).
    """
    ventas_row = await repo.get_resumen_diario_ventas(db)
    if ventas_row is None:
        return None

    top_productos = await repo.get_top_productos_diario(db)
    top_insumos = await repo.get_top_insumos_diario(db)
    horas = await repo.get_horas_diario(db)

    recomendacion = None
    if incluir_recomendacion:
        recomendacion_rows = await repo.get_recomendacion_compra(db)
        recomendacion = [
            {
                "id_insumo": r.id_insumo,
                "nombre": r.nombre_insumo,
                "unidad": r.unidad,
                "stock_actual": r.stock_actual,
                "consumo_bruto_diario": r.consumo_bruto_diario,
                "punto_pedido": r.punto_pedido,
                "dispara_pedido": r.dispara_pedido,
                "cantidad_a_comprar": r.cantidad_a_comprar,
            }
            for r in recomendacion_rows
        ]

    return DashboardDiarioSchema(
        fecha_analisis=ventas_row.fecha,
        actualizado_a=ventas_row.actualizado_a,
        ventas=VentasDiariasSchema(
            ingreso=ventas_row.ingreso,
            unidades=ventas_row.unidades,
            num_pedidos=ventas_row.num_pedidos,
            promedio_venta_pedido=ventas_row.promedio_venta_pedido,
            referencia=ReferenciaVentasSchema(
                ingreso=ventas_row.ref_ingreso,
                unidades=ventas_row.ref_unidades,
                promedio_venta_pedido=ventas_row.ref_promedio_pedido,
            ),
            variacion=VariacionVentasSchema(
                ingreso_pct=ventas_row.var_ingreso_pct,
                promedio_venta_pedido_pct=ventas_row.var_promedio_pedido_pct,
            ),
        ),
        merma=MermaSchema(valor=ventas_row.merma_valor),
        top_productos=[TopProductoSchema.model_validate(p) for p in top_productos],
        top_insumos=[TopInsumoSchema.model_validate(i) for i in top_insumos],
        ventas_por_hora=[VentaHoraSchema.model_validate(h) for h in horas],
        recomendacion_compra=recomendacion,
    )


async def get_dashboard_mensual(
    db: AsyncSession, mes: date, incluir_mes_anterior: bool = True
) -> DashboardMensualSchema | None:
    """Assemble the monthly dashboard (GET /bi/dashboard/mensual, §4.1).

    Args:
        db: Async database session.
        mes: First day of the target month.
        incluir_mes_anterior: If True, recursively includes the
            previous closed month (only for the default dashboard;
            GET /bi/mensual omits this, per §4.2).

    Returns:
        DashboardMensualSchema, or None if that month has no data
        (bi.resumen_mensual_meta has no row for it).
    """
    meta = await repo.get_resumen_mensual_meta(db, mes)
    if meta is None:
        return None

    ranking = await repo.get_ranking_mensual(db, mes)
    heatmap = await repo.get_heatmap_mensual(db, mes)
    senales = await repo.get_senales_precio_mensual(db, mes)
    warnings = await repo.get_warnings_insumo_mensual(db, mes)
    insumos = await repo.get_resumen_insumo_mensual(db, mes)

    top_producto = None
    if ranking:
        top = max(ranking, key=lambda r: r.unidades or 0)
        top_producto = TopProductoMesSchema(
            id_producto=top.id_producto,
            nombre=top.nombre,
            unidades=top.unidades,
        )

    top_insumo = None
    if insumos:
        top_i = max(insumos, key=lambda i: i.valor_consumo or 0)
        top_insumo = TopInsumoMesSchema(
            id_insumo=top_i.id_insumo,
            nombre=top_i.nombre,
            valor_consumo=top_i.valor_consumo,
            cantidad=top_i.cantidad,
            unidad=top_i.unidad,
        )

    mes_anterior = None
    if incluir_mes_anterior:
        mes_prev = (mes.replace(day=1) - timedelta(days=1)).replace(day=1)
        mes_anterior = await get_dashboard_mensual(
            db, mes_prev, incluir_mes_anterior=False
        )

    return DashboardMensualSchema(
        mes=mes.strftime("%Y-%m"),
        parcial=meta.parcial,
        dias_con_datos=meta.dias_con_datos,
        actualizado_a=meta.actualizado_a,
        ranking_cantidad=[RankingCantidadSchema.model_validate(r) for r in ranking],
        ganancia_bruta=[GananciaBrutaSchema.model_validate(r) for r in ranking],
        top_producto=top_producto,
        top_insumo=top_insumo,
        picos=[PicoHoraSchema.model_validate(h) for h in heatmap],
        senales_precio=[SenalPrecioSchema.model_validate(s) for s in senales],
        warnings_insumo=[WarningInsumoSchema.model_validate(w) for w in warnings],
        fugas=[FugaInsumoSchema.model_validate(i) for i in insumos],
        mes_anterior=mes_anterior,
    )


async def procesar_dia(
    fecha: date | None, db: AsyncSession, origen: str = "manual"
) -> ProcesarDiaResponse:
    """Run the BI ETL pipeline for a given date (POST /bi/procesar-dia, §4.4).

    Defaults to yesterday in Colombia local time if no date is provided.

    Args:
        fecha: The business day to process. Defaults to yesterday (COT).
        db: Async database session.
        origen: One of 'cron', 'retrigger', 'manual'. Defaults to
            'manual' for direct API calls (the cron endpoint passes
            'cron' explicitly).

    Returns:
        ProcesarDiaResponse with ok, id_ejecucion, fecha_procesada,
        and status.
    """
    fecha_a_procesar = fecha or _fecha_ayer()

    resultado = await etl_service.procesar_dia(fecha_a_procesar, db, origen=origen)

    return ProcesarDiaResponse(
        ok=resultado["ok"],
        id_ejecucion=resultado["id_ejecucion"],
        fecha_procesada=fecha_a_procesar,
        status=resultado["status"],
    )


async def get_diario_puntual(
    db: AsyncSession, fecha: date
) -> DashboardDiarioSchema | None:
    """Compute the daily dashboard for a historical date (GET /bi/diario, §4.2).

    Unlike get_dashboard_diario (which reads precomputed
    bi.resumen_diario_*), this calculates on the fly from
    bi.kpi_*_dia using the same formulas (queries.py), since
    resumen_diario_* only holds yesterday's snapshot.

    Always omits recomendacion_compra (§2.3 — purchase recommendations
    don't apply to historical dates).

    Args:
        db: Async database session.
        fecha: The historical date to analyze.

    Returns:
        DashboardDiarioSchema with recomendacion_compra=None, or None
        if no ETL data exists for this date (bi.kpi_producto_dia has
        no rows for fecha).
    """
    if not await queries.existe_datos_dia(db, fecha):
        return None

    ventas = await queries.calcular_ventas(db, fecha, fecha)
    top_productos = await queries.calcular_top_productos(db, fecha, fecha)
    top_insumos = await queries.calcular_top_insumos(db, fecha, fecha)
    horas = await queries.calcular_horas(db, fecha, fecha)

    return DashboardDiarioSchema(
        fecha_analisis=fecha,
        actualizado_a=datetime.now(tz=BOGOTA_TZ),
        ventas=VentasDiariasSchema(
            ingreso=ventas.get("ingreso", 0),
            unidades=ventas.get("unidades", 0),
            num_pedidos=ventas.get("num_pedidos", 0),
            promedio_venta_pedido=ventas.get("promedio_venta_pedido"),
            referencia=ReferenciaVentasSchema(
                ingreso=ventas.get("ref_ingreso"),
                unidades=ventas.get("ref_unidades"),
                promedio_venta_pedido=ventas.get("ref_promedio_pedido"),
            ),
            variacion=VariacionVentasSchema(
                ingreso_pct=ventas.get("var_ingreso_pct"),
                promedio_venta_pedido_pct=ventas.get("var_promedio_pedido_pct"),
            ),
        ),
        merma=MermaSchema(valor=ventas.get("merma_valor", 0)),
        top_productos=[TopProductoSchema(**p) for p in top_productos],
        top_insumos=[TopInsumoSchema(**i) for i in top_insumos],
        ventas_por_hora=[VentaHoraSchema(**h) for h in horas],
        recomendacion_compra=None,
    )


async def get_meta(db: AsyncSession) -> MetaSchema:
    """Return the available date range for the front's selectors (GET /bi/meta).

    historico_desde: earliest date with a successful ETL run.
    ultimo_dia_procesado: most recent date with a successful ETL run.

    Args:
        db: Async database session.

    Returns:
        MetaSchema with historico_desde and ultimo_dia_procesado.
    """
    primera = await repo.get_primera_fecha_procesada(db)
    ultima_ejecucion = await repo.get_ultima_ejecucion_exitosa(db)

    return MetaSchema(
        historico_desde=primera or date.today(),
        ultimo_dia_procesado=(
            ultima_ejecucion.fecha_procesada if ultima_ejecucion else date.today()
        ),
    )


async def get_ejecuciones_etl(
    db: AsyncSession, limit: int = 30
) -> list[EjecucionEtlSchema]:
    """Return recent ETL run history (GET /bi/admin/etl/ejecuciones, §4.4).

    Args:
        db: Async database session.
        limit: Maximum number of rows to return (default 30).

    Returns:
        List of EjecucionEtlSchema, most recent first.
    """
    rows = await repo.get_ejecuciones_etl(db, limit)
    return [EjecucionEtlSchema(**row) for row in rows]


async def get_mensual_puntual(
    db: AsyncSession, mes: date
) -> DashboardMensualSchema | None:
    """Return the monthly dashboard for a specific closed month (GET /bi/mensual, §4.2).

    Same as get_dashboard_mensual but without mes_anterior — closed
    months already have their resumen_mensual_* rows from when the
    ETL processed them (no on-the-fly calculation needed, per
    coordination decision).

    Args:
        db: Async database session.
        mes: First day of the target month.

    Returns:
        DashboardMensualSchema without mes_anterior, or None if that
        month was never processed.
    """
    return await get_dashboard_mensual(db, mes, incluir_mes_anterior=False)
