"""BI reusable query functions, parametrized by date range.

Extracted from etl_service.py's _paso5a_resumenes_diarios queries
(D1-D4), generalized to accept [desde, hasta] instead of a fixed
:fecha. Used by:
  - etl_service.py (paso5a): desde == hasta == fecha, result is
    INSERTed into bi.resumen_diario_*.
  - service.py (Explorar §4.2): desde/hasta from query params,
    result is returned directly (no INSERT).

This is the SINGLE SOURCE for these formulas — do not duplicate.
Any formula fix here automatically applies to both the nightly
ETL and the Explorar endpoints.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def calcular_ventas(db: AsyncSession, desde: date, hasta: date) -> dict:
    """Compute the resumen_diario_ventas shape for a date range.

    For a single day (desde == hasta), this is D1's exact formula.
    For a range, ingreso/unidades/num_pedidos/merma_valor are summed
    across all days; the reference (4 same-weekday) is computed
    relative to `desde`.

    Args:
        db: Async database session.
        desde: First day of the range (inclusive).
        hasta: Last day of the range (inclusive).

    Returns:
        Dict with keys: ingreso, unidades, num_pedidos,
        promedio_venta_pedido, ref_ingreso, ref_unidades,
        ref_promedio_pedido, var_ingreso_pct,
        var_promedio_pedido_pct, merma_valor.
    """
    result = await db.execute(
        text("""
        WITH ventas AS (
            SELECT
                COALESCE(SUM(ingreso), 0)  AS ingreso,
                COALESCE(SUM(unidades), 0) AS unidades
            FROM bi.kpi_producto_dia
            WHERE fecha BETWEEN :desde AND :hasta
        ),
        pedidos AS (
            SELECT COALESCE(SUM(num_ventas), 0) AS num_pedidos
            FROM bi.kpi_venta_hora_dia
            WHERE fecha BETWEEN :desde AND :hasta
        ),
        merma AS (
            SELECT COALESCE(
                SUM(merma_registrada * precio_real), 0
            ) AS merma_valor
            FROM bi.kpi_insumo_dia
            WHERE fecha BETWEEN :desde AND :hasta
        ),
        ref_fechas AS (
            SELECT DISTINCT fecha
            FROM bi.kpi_producto_dia
            WHERE fecha < :desde
              AND EXTRACT(DOW FROM fecha)
                  = EXTRACT(DOW FROM :desde::date)
            ORDER BY fecha DESC
            LIMIT 4
        ),
        ref_dias AS (
            SELECT
                p.fecha,
                SUM(p.ingreso)  AS ingreso,
                SUM(p.unidades) AS unidades,
                CASE WHEN SUM(h.num_ventas) > 0
                     THEN SUM(p.ingreso) / SUM(h.num_ventas)
                END AS prom_pedido
            FROM bi.kpi_producto_dia p
            JOIN (
                SELECT fecha, SUM(num_ventas) AS num_ventas
                FROM bi.kpi_venta_hora_dia
                GROUP BY fecha
            ) h ON h.fecha = p.fecha
            WHERE p.fecha IN (SELECT fecha FROM ref_fechas)
            GROUP BY p.fecha
        ),
        refs AS (
            SELECT
                AVG(ingreso)     AS ref_ingreso,
                AVG(unidades)    AS ref_unidades,
                AVG(prom_pedido) AS ref_promedio_pedido
            FROM ref_dias
        )
        SELECT
            v.ingreso,
            v.unidades,
            p.num_pedidos,
            CASE WHEN p.num_pedidos > 0
                 THEN v.ingreso / p.num_pedidos
            END AS promedio_venta_pedido,
            r.ref_ingreso,
            r.ref_unidades,
            r.ref_promedio_pedido,
            CASE WHEN r.ref_ingreso > 0
                 THEN (v.ingreso - r.ref_ingreso)
                      / r.ref_ingreso * 100
            END AS var_ingreso_pct,
            CASE WHEN r.ref_promedio_pedido > 0
                      AND p.num_pedidos > 0
                 THEN ((v.ingreso / p.num_pedidos)
                       - r.ref_promedio_pedido)
                      / r.ref_promedio_pedido * 100
            END AS var_promedio_pedido_pct,
            m.merma_valor
        FROM ventas v, pedidos p, merma m, refs r
    """),
        {"desde": desde, "hasta": hasta},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def calcular_top_productos(
    db: AsyncSession, desde: date, hasta: date, limite: int = 3
) -> list[dict]:
    """Compute the resumen_diario_top_producto shape for a date range.

    For a single day (desde == hasta), this is D2's exact formula.
    For a range, unidades/ingreso are summed across all days before
    ranking — the "top N" reflects the whole range, not per-day.

    Args:
        db: Async database session.
        desde: First day of the range (inclusive).
        hasta: Last day of the range (inclusive).
        limite: Max number of products to return (3 for the dashboard
            podium, per §4.1).

    Returns:
        List of dicts with posicion, id_producto, nombre, unidades,
        ingreso — ordered by posicion ascending.
    """
    result = await db.execute(
        text("""
        WITH agregado AS (
            SELECT
                id_producto,
                MAX(nombre_producto) AS nombre,
                SUM(unidades)        AS unidades,
                SUM(ingreso)         AS ingreso
            FROM bi.kpi_producto_dia
            WHERE fecha BETWEEN :desde AND :hasta
            GROUP BY id_producto
        ),
        ranked AS (
            SELECT
                id_producto,
                nombre,
                unidades,
                ingreso,
                ROW_NUMBER() OVER (
                    ORDER BY unidades DESC,
                             ingreso DESC,
                             id_producto ASC
                ) AS posicion
            FROM agregado
        )
        SELECT posicion, id_producto, nombre, unidades, ingreso
        FROM ranked
        WHERE posicion <= :limite
        ORDER BY posicion
    """),
        {"desde": desde, "hasta": hasta, "limite": limite},
    )
    return [dict(row) for row in result.mappings().all()]
