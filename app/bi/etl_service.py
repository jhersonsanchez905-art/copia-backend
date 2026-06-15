"""BI ETL service for daily metric processing.

Implements procesar_dia(fecha, db): reads from pos.* schema,
upserts into bi fact tables, rebuilds all summary tables,
and notifies Vercel to purge the BI metrics cache.

Execution order:
    1. kpi_producto_dia     — daily margin per product
    2. kpi_venta_hora_dia   — hourly sales heatmap
    3. kpi_insumo_dia       — ingredient snapshot + consumption
    4. kpi_consumo_insumo_producto_dia — ingredient breakdown by product
    5. rebuild_resumenes    — DELETE + INSERT for all 6 summary tables
    6. notify_vercel        — best-effort cache purge webhook

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging
from datetime import date, timedelta, timezone

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.config import settings

logger = logging.getLogger(__name__)

BOGOTA_TZ = ZoneInfo("America/Bogota")


def _ventana_utc(fecha_local: date) -> tuple:
    """Convert a local Colombia date to UTC window boundaries.

    Args:
        fecha_local: The business day in Colombia local time.

    Returns:
        Tuple of (inicio_utc, fin_utc) as ISO strings for SQL binding.
    """
    from datetime import datetime

    inicio = datetime(
        fecha_local.year,
        fecha_local.month,
        fecha_local.day,
        tzinfo=BOGOTA_TZ,
    ).astimezone(timezone.utc)
    fin = inicio + timedelta(days=1)
    return inicio, fin


async def _paso1_kpi_producto_dia(
    db: AsyncSession,
    fecha: date,
    v_ini: str,
    v_fin: str,
) -> None:
    """Upsert daily product KPIs with real cost recalculated from ingredients.

    Cost formula per ingredient unit:
        costo_udm = (precio / contador_unidades) * 100 / pct_rendimiento

    Uses the recipe version frozen at sale time (iv.id_receta_version),
    not the current active version. This ensures accurate historical margins.

    Args:
        db: Async database session.
        fecha: Business day being processed (Colombia local).
        v_ini: UTC window start as ISO string.
        v_fin: UTC window end as ISO string.
    """
    sql = text("""
        WITH costo_udm AS (
            SELECT
                i.id_insumo,
                CASE
                    WHEN i.pct_rendimiento > 0
                    THEN (i.precio / COALESCE(NULLIF(i.contador_unidades, 0), 1))
                         * 100.0 / i.pct_rendimiento
                    ELSE i.precio / COALESCE(NULLIF(i.contador_unidades, 0), 1)
                END AS costo_udm_real
            FROM pos.insumo i
        ),
        costo_directos AS (
            SELECT
                rdi.id_receta_version,
                SUM(rdi.cantidad * cu.costo_udm_real) AS costo_real
            FROM pos.receta_detalle_insumo rdi
            JOIN costo_udm cu ON cu.id_insumo = rdi.id_insumo
            GROUP BY rdi.id_receta_version
        ),
        costo_subrecetas AS (
            SELECT
                rds.id_receta_version,
                SUM(
                    (si.cantidad / NULLIF(sr.porciones, 0))
                    * rds.cantidad
                    * cu.costo_udm_real
                ) AS costo_real
            FROM pos.receta_detalle_subreceta rds
            JOIN pos.subreceta sr             ON sr.id_subreceta = rds.id_subreceta
            JOIN pos.subreceta_ingrediente si ON si.id_subreceta = rds.id_subreceta
            JOIN costo_udm cu                 ON cu.id_insumo = si.id_insumo
            GROUP BY rds.id_receta_version
        ),
        costo_real AS (
            SELECT
                rv.id_receta_version,
                COALESCE(d.costo_real, 0) + COALESCE(s.costo_real, 0) AS costo_unitario
            FROM pos.receta_version rv
            LEFT JOIN costo_directos   d ON d.id_receta_version = rv.id_receta_version
            LEFT JOIN costo_subrecetas s ON s.id_receta_version = rv.id_receta_version
        )
        INSERT INTO bi.kpi_producto_dia
            (fecha, id_producto, nombre_producto,
             unidades, ingreso, costo, margen, margen_pct)
        SELECT
            :fecha,
            iv.id_producto,
            MAX(pr.nombre),
            SUM(iv.cantidad),
            SUM(iv.precio_unitario * iv.cantidad),
            SUM(cr.costo_unitario * iv.cantidad),
            SUM((iv.precio_unitario - cr.costo_unitario) * iv.cantidad),
            CASE
                WHEN SUM(iv.precio_unitario * iv.cantidad) > 0
                THEN SUM((iv.precio_unitario - cr.costo_unitario) * iv.cantidad)
                     / SUM(iv.precio_unitario * iv.cantidad) * 100
            END
        FROM pos.item_venta iv
        JOIN pos.venta v               ON v.id_venta = iv.id_venta
        JOIN pos.producto pr           ON pr.id_producto = iv.id_producto
        JOIN costo_real cr             ON cr.id_receta_version = iv.id_receta_version
        WHERE v.fecha >= :v_ini
          AND v.fecha <  :v_fin
          AND v.estado = 'completada'
        GROUP BY iv.id_producto
        ON CONFLICT (fecha, id_producto) DO UPDATE SET
            nombre_producto = EXCLUDED.nombre_producto,
            unidades        = EXCLUDED.unidades,
            ingreso         = EXCLUDED.ingreso,
            costo           = EXCLUDED.costo,
            margen          = EXCLUDED.margen,
            margen_pct      = EXCLUDED.margen_pct
    """)
    await db.execute(sql, {"fecha": fecha, "v_ini": v_ini, "v_fin": v_fin})


async def _paso2_kpi_venta_hora_dia(
    db: AsyncSession,
    fecha: date,
    v_ini: str,
    v_fin: str,
) -> None:
    """Upsert hourly sales KPIs converted to Colombia local time.

    venta.fecha is stored in UTC. Hours are extracted after converting
    to America/Bogota (UTC-5, no DST).

    num_ventas = COUNT(DISTINCT id_venta) — pedidos distintos en la hora,
    usado para promedio_venta_pedido (§2.4.2).

    Args:
        db: Async database session.
        fecha: Business day being processed (Colombia local).
        v_ini: UTC window start as ISO string.
        v_fin: UTC window end as ISO string.
    """
    sql = text("""
        INSERT INTO bi.kpi_venta_hora_dia
            (fecha, hora, dia_semana, unidades, ingreso, num_ventas)
        SELECT
            :fecha,
            EXTRACT(HOUR FROM v.fecha AT TIME ZONE 'America/Bogota')::smallint,
            EXTRACT(DOW FROM :fecha::date)::smallint,
            SUM(iv.cantidad),
            SUM(iv.precio_unitario * iv.cantidad),
            COUNT(DISTINCT v.id_venta)
        FROM pos.venta v
        JOIN pos.item_venta iv ON iv.id_venta = v.id_venta
        WHERE v.fecha >= :v_ini
          AND v.fecha <  :v_fin
          AND v.estado = 'completada'
        GROUP BY EXTRACT(HOUR FROM v.fecha AT TIME ZONE 'America/Bogota')
        ON CONFLICT (fecha, hora) DO UPDATE SET
            dia_semana = EXCLUDED.dia_semana,
            unidades   = EXCLUDED.unidades,
            ingreso    = EXCLUDED.ingreso,
            num_ventas = EXCLUDED.num_ventas
    """)
    await db.execute(sql, {"fecha": fecha, "v_ini": v_ini, "v_fin": v_fin})


async def _paso3_kpi_insumo_dia(
    db: AsyncSession,
    fecha: date,
    v_ini: str,
    v_fin: str,
) -> None:
    """Upsert daily ingredient snapshot with stock and consumption.

    Key decisions (corrected 2026-06-14, see C1/C2 in bi-logic review):
    - stock_actual: from pos.stock (1:1 with insumo, UNIQUE constraint).
    - pct_rendimiento: stored as FRACTION (0-1), normalized from pos.insumo's
      0-100 scale. All downstream bi.* tables consume the fraction.
    - precio_real: precio / (pct_rendimiento_fraccion), guard pct > 0.
    - consumo_neto: SUM where tipo='salida' AND id_venta IS NOT NULL
      (consumption tied to actual sales — C2 separator).
    - merma_registrada: SUM where tipo='merma' ONLY (C2 fix — excludes
      negative inventory adjustments, which are tipo='salida' with
      id_venta IS NULL but are NOT spoilage).
    - consumo_bruto: consumo_neto / pct_rendimiento_fraccion (theoretical).
    - Only active ingredients (insumo.activo = TRUE).

    Args:
        db: Async database session.
        fecha: Business day being processed (Colombia local).
        v_ini: UTC window start as ISO string.
        v_fin: UTC window end as ISO string.
    """
    sql = text("""
        INSERT INTO bi.kpi_insumo_dia
            (fecha, id_insumo, nombre_insumo, stock_actual,
             stock_minimo, stock_maximo, dias_anticipacion,
             pct_rendimiento, precio, precio_real,
             consumo_neto, consumo_bruto, merma_registrada)
        SELECT
            :fecha,
            i.id_insumo,
            i.nombre,
            COALESCE(st.cantidad, 0),
            i.stock_minimo,
            i.stock_maximo,
            i.dias_anticipacion,
            CASE
                WHEN i.pct_rendimiento > 0
                THEN i.pct_rendimiento / 100.0
                ELSE 0
            END,
            i.precio,
            CASE
                WHEN i.pct_rendimiento > 0
                THEN i.precio / (i.pct_rendimiento / 100.0)
                ELSE NULL
            END,
            COALESCE(m.consumo_neto, 0),
            CASE
                WHEN i.pct_rendimiento > 0
                THEN COALESCE(m.consumo_neto, 0) / (i.pct_rendimiento / 100.0)
                ELSE COALESCE(m.consumo_neto, 0)
            END,
            COALESCE(m.merma_registrada, 0)
        FROM pos.insumo i
        LEFT JOIN pos.stock st ON st.id_insumo = i.id_insumo
        LEFT JOIN (
            SELECT
                id_insumo,
                SUM(cantidad) FILTER (
                    WHERE tipo = 'salida' AND id_venta IS NOT NULL
                ) AS consumo_neto,
                SUM(cantidad) FILTER (
                    WHERE tipo = 'merma'
                ) AS merma_registrada
            FROM pos.movimiento_inventario
            WHERE fecha >= :v_ini
              AND fecha <  :v_fin
            GROUP BY id_insumo
        ) m ON m.id_insumo = i.id_insumo
        WHERE i.activo = TRUE
        ON CONFLICT (fecha, id_insumo) DO UPDATE SET
            nombre_insumo     = EXCLUDED.nombre_insumo,
            stock_actual      = EXCLUDED.stock_actual,
            stock_minimo      = EXCLUDED.stock_minimo,
            stock_maximo      = EXCLUDED.stock_maximo,
            dias_anticipacion = EXCLUDED.dias_anticipacion,
            pct_rendimiento   = EXCLUDED.pct_rendimiento,
            precio            = EXCLUDED.precio,
            precio_real       = EXCLUDED.precio_real,
            consumo_neto      = EXCLUDED.consumo_neto,
            consumo_bruto     = EXCLUDED.consumo_bruto,
            merma_registrada  = EXCLUDED.merma_registrada
    """)
    await db.execute(sql, {"fecha": fecha, "v_ini": v_ini, "v_fin": v_fin})


async def _paso4_kpi_consumo_insumo_producto(
    db: AsyncSession,
    fecha: date,
    v_ini: str,
    v_fin: str,
) -> None:
    """Upsert ingredient consumption broken down by product.

    Covers direct ingredients and ingredients via subrecipes (one level).
    Subrecipe formula (confirmed in venta_service.py):
        consumo = (si.cantidad / sr.porciones) * rds.cantidad * iv.cantidad

    Args:
        db: Async database session.
        fecha: Business day being processed (Colombia local).
        v_ini: UTC window start as ISO string.
        v_fin: UTC window end as ISO string.
    """
    sql = text("""
        INSERT INTO bi.kpi_consumo_insumo_producto_dia
            (fecha, id_insumo, id_producto, consumo)
        WITH directos AS (
            SELECT
                iv.id_producto,
                rdi.id_insumo,
                rdi.cantidad * iv.cantidad AS consumo
            FROM pos.item_venta iv
            JOIN pos.venta v ON v.id_venta = iv.id_venta
            JOIN pos.receta_detalle_insumo rdi
                ON rdi.id_receta_version = iv.id_receta_version
            WHERE v.fecha >= :v_ini
              AND v.fecha <  :v_fin
              AND v.estado = 'completada'
        ),
        via_subreceta AS (
            SELECT
                iv.id_producto,
                si.id_insumo,
                (si.cantidad / NULLIF(sr.porciones, 0))
                    * rds.cantidad
                    * iv.cantidad AS consumo
            FROM pos.item_venta iv
            JOIN pos.venta v ON v.id_venta = iv.id_venta
            JOIN pos.receta_detalle_subreceta rds
                ON rds.id_receta_version = iv.id_receta_version
            JOIN pos.subreceta sr
                ON sr.id_subreceta = rds.id_subreceta
            JOIN pos.subreceta_ingrediente si
                ON si.id_subreceta = rds.id_subreceta
            WHERE v.fecha >= :v_ini
              AND v.fecha <  :v_fin
              AND v.estado = 'completada'
        )
        SELECT :fecha, id_insumo, id_producto, SUM(consumo)
        FROM (
            SELECT * FROM directos
            UNION ALL
            SELECT * FROM via_subreceta
        ) todos
        GROUP BY id_producto, id_insumo
        ON CONFLICT (fecha, id_insumo, id_producto) DO UPDATE SET
            consumo = EXCLUDED.consumo
    """)
    await db.execute(sql, {"fecha": fecha, "v_ini": v_ini, "v_fin": v_fin})


async def _paso5_rebuild_resumenes(
    db: AsyncSession,
    fecha: date,
) -> None:
    """Rebuild all summary tables (daily + monthly) in a transaction.

    Daily summaries (5): full DELETE + INSERT — singleton snapshot of
    ``fecha`` (no fecha in PK, rebuilt completely each night).

    Monthly summaries (7): DELETE WHERE mes = :mes + INSERT — only the
    current month is rewritten; closed months are immutable (§2.3).

    Uses DELETE + INSERT (not TRUNCATE) to stay within the transaction
    boundary. MVCC ensures readers never see empty tables.

    Args:
        db: Async database session (transaction managed by caller).
        fecha: Business day being processed (Colombia local). Defines
            both the daily snapshot and the month for monthly summaries.
    """
    mes = fecha.replace(day=1)
    params = {"fecha": fecha, "mes": mes}

    # ══════════════════════════════════════════════════════════════════
    # BLOQUE A · RESÚMENES DIARIOS (5 tablas)
    # ══════════════════════════════════════════════════════════════════

    # ── D1: resumen_diario_ventas ─────────────────────────────────────
    await db.execute(text("DELETE FROM bi.resumen_diario_ventas"))
    await db.execute(
        text("""
        WITH ventas AS (
            SELECT
                COALESCE(SUM(ingreso), 0)  AS ingreso,
                COALESCE(SUM(unidades), 0) AS unidades
            FROM bi.kpi_producto_dia
            WHERE fecha = :fecha
        ),
        pedidos AS (
            SELECT COALESCE(SUM(num_ventas), 0) AS num_pedidos
            FROM bi.kpi_venta_hora_dia
            WHERE fecha = :fecha
        ),
        merma AS (
            SELECT COALESCE(
                SUM(merma_registrada * precio_real), 0
            ) AS merma_valor
            FROM bi.kpi_insumo_dia
            WHERE fecha = :fecha
        ),
        ref_fechas AS (
            SELECT DISTINCT fecha
            FROM bi.kpi_producto_dia
            WHERE fecha < :fecha
              AND EXTRACT(DOW FROM fecha)
                  = EXTRACT(DOW FROM :fecha::date)
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
        INSERT INTO bi.resumen_diario_ventas
            (fecha, ingreso, unidades, num_pedidos,
             promedio_venta_pedido,
             ref_ingreso, ref_unidades, ref_promedio_pedido,
             var_ingreso_pct, var_promedio_pedido_pct,
             merma_valor, actualizado_a)
        SELECT
            :fecha,
            v.ingreso,
            v.unidades,
            p.num_pedidos,
            CASE WHEN p.num_pedidos > 0
                 THEN v.ingreso / p.num_pedidos
            END,
            r.ref_ingreso,
            r.ref_unidades,
            r.ref_promedio_pedido,
            CASE WHEN r.ref_ingreso > 0
                 THEN (v.ingreso - r.ref_ingreso)
                      / r.ref_ingreso * 100
            END,
            CASE WHEN r.ref_promedio_pedido > 0
                      AND p.num_pedidos > 0
                 THEN ((v.ingreso / p.num_pedidos)
                       - r.ref_promedio_pedido)
                      / r.ref_promedio_pedido * 100
            END,
            m.merma_valor,
            now()
        FROM ventas v, pedidos p, merma m, refs r
    """),
        params,
    )

    # ── D2: resumen_diario_top_producto ───────────────────────────────
    await db.execute(text("DELETE FROM bi.resumen_diario_top_producto"))
    await db.execute(
        text("""
        WITH ranked AS (
            SELECT
                id_producto,
                nombre_producto AS nombre,
                unidades,
                ingreso,
                ROW_NUMBER() OVER (
                    ORDER BY unidades DESC,
                             ingreso DESC,
                             id_producto ASC
                ) AS posicion
            FROM bi.kpi_producto_dia
            WHERE fecha = :fecha
        )
        INSERT INTO bi.resumen_diario_top_producto
            (posicion, id_producto, nombre, unidades, ingreso)
        SELECT posicion, id_producto, nombre, unidades, ingreso
        FROM ranked
        WHERE posicion <= 3
    """),
        params,
    )

    # ── D3: resumen_diario_top_insumo ─────────────────────────────────
    await db.execute(text("DELETE FROM bi.resumen_diario_top_insumo"))
    await db.execute(
        text("""
        WITH ranked AS (
            SELECT
                k.id_insumo,
                k.nombre_insumo AS nombre,
                k.consumo_neto * k.precio_real AS valor_consumo,
                k.consumo_neto AS cantidad,
                COALESCE(um.nombre, '') AS unidad,
                k.merma_registrada * k.precio_real AS merma_valor,
                ROW_NUMBER() OVER (
                    ORDER BY k.consumo_neto * k.precio_real DESC,
                             k.consumo_neto DESC,
                             k.id_insumo ASC
                ) AS posicion
            FROM bi.kpi_insumo_dia k
            LEFT JOIN pos.insumo i
                ON i.id_insumo = k.id_insumo
            LEFT JOIN pos.unidad_medida um
                ON um.id_unidad_medida = i.id_unidad_medida
            WHERE k.fecha = :fecha
        )
        INSERT INTO bi.resumen_diario_top_insumo
            (posicion, id_insumo, nombre,
             valor_consumo, cantidad, unidad, merma_valor)
        SELECT posicion, id_insumo, nombre,
               valor_consumo, cantidad, unidad, merma_valor
        FROM ranked
        WHERE posicion <= 5
    """),
        params,
    )

    # ── D4: resumen_diario_horas ──────────────────────────────────────
    await db.execute(text("DELETE FROM bi.resumen_diario_horas"))
    await db.execute(
        text("""
        WITH actual AS (
            SELECT hora, unidades, ingreso
            FROM bi.kpi_venta_hora_dia
            WHERE fecha = :fecha
        ),
        patron AS (
            SELECT
                hora,
                AVG(unidades) AS patron_unidades,
                AVG(ingreso)  AS patron_ingreso
            FROM bi.kpi_venta_hora_dia
            WHERE fecha < :fecha
              AND EXTRACT(DOW FROM fecha)
                  = EXTRACT(DOW FROM :fecha::date)
              AND fecha >= :fecha - INTERVAL '90 days'
            GROUP BY hora
        ),
        horas AS (
            SELECT generate_series(0, 23) AS hora
        )
        INSERT INTO bi.resumen_diario_horas
            (hora, unidades, ingreso,
             patron_unidades, patron_ingreso)
        SELECT
            h.hora,
            a.unidades,
            a.ingreso,
            p.patron_unidades,
            p.patron_ingreso
        FROM horas h
        LEFT JOIN actual a ON a.hora = h.hora
        LEFT JOIN patron p ON p.hora = h.hora
    """),
        params,
    )

    # ── D5: resumen_recomendacion_compra ──────────────────────────────
    await db.execute(text("DELETE FROM bi.resumen_recomendacion_compra"))
    await db.execute(
        text("""
        WITH ritmo AS (
            SELECT
                id_insumo,
                SUM(consumo_bruto) / 28.0 AS consumo_bruto_diario
            FROM bi.kpi_insumo_dia
            WHERE fecha > :fecha - INTERVAL '28 days'
              AND fecha <= :fecha
            GROUP BY id_insumo
        )
        INSERT INTO bi.resumen_recomendacion_compra
            (id_insumo, nombre_insumo, unidad, stock_actual,
             consumo_bruto_diario, punto_pedido,
             dispara_pedido, cantidad_a_comprar)
        SELECT
            i.id_insumo,
            i.nombre,
            COALESCE(um.nombre, ''),
            COALESCE(st.cantidad, 0),
            COALESCE(r.consumo_bruto_diario, 0),
            COALESCE(r.consumo_bruto_diario, 0)
                * COALESCE(i.dias_anticipacion, 0)
                + i.stock_minimo,
            COALESCE(st.cantidad, 0) <= (
                COALESCE(r.consumo_bruto_diario, 0)
                * COALESCE(i.dias_anticipacion, 0)
                + i.stock_minimo
            ),
            GREATEST(
                COALESCE(r.consumo_bruto_diario, 0) * 7 * 1.20
                    - COALESCE(st.cantidad, 0),
                0
            )
        FROM pos.insumo i
        LEFT JOIN pos.stock st
            ON st.id_insumo = i.id_insumo
        LEFT JOIN pos.unidad_medida um
            ON um.id_unidad_medida = i.id_unidad_medida
        LEFT JOIN ritmo r
            ON r.id_insumo = i.id_insumo
        WHERE i.activo = TRUE
    """),
        params,
    )

    # ══════════════════════════════════════════════════════════════════
    # BLOQUE B · RESÚMENES MENSUALES (7 tablas)
    # Solo se reescribe el mes en curso; meses cerrados son inmutables.
    # ══════════════════════════════════════════════════════════════════

    # ── M1: resumen_mensual_meta ──────────────────────────────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_meta WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        INSERT INTO bi.resumen_mensual_meta
            (mes, parcial, dias_con_datos, actualizado_a)
        SELECT
            :mes,
            (:mes = date_trunc('month', CURRENT_DATE)::date),
            COUNT(DISTINCT fecha),
            now()
        FROM bi.kpi_producto_dia
        WHERE fecha >= :mes
          AND fecha < :mes + INTERVAL '1 month'
    """),
        params,
    )

    # ── M2: resumen_mensual_ranking ───────────────────────────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_ranking WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        INSERT INTO bi.resumen_mensual_ranking
            (mes, id_producto, nombre, unidades, ingreso,
             ganancia_bruta, margen_pct)
        SELECT
            :mes,
            id_producto,
            MAX(nombre_producto),
            SUM(unidades),
            SUM(ingreso),
            SUM(margen),
            CASE WHEN SUM(ingreso) > 0
                 THEN SUM(margen) / SUM(ingreso) * 100
            END
        FROM bi.kpi_producto_dia
        WHERE fecha >= :mes
          AND fecha < :mes + INTERVAL '1 month'
        GROUP BY id_producto
    """),
        params,
    )

    # ── M3: resumen_mensual_heatmap ───────────────────────────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_heatmap WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        INSERT INTO bi.resumen_mensual_heatmap
            (mes, dia_semana, hora, unidades_prom, ingreso_prom)
        SELECT
            :mes,
            dia_semana,
            hora,
            AVG(unidades),
            AVG(ingreso)
        FROM bi.kpi_venta_hora_dia
        WHERE fecha >= :mes
          AND fecha < :mes + INTERVAL '1 month'
        GROUP BY dia_semana, hora
    """),
        params,
    )

    # ── M4: resumen_mensual_senal_precio ──────────────────────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_senal_precio WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        WITH base AS (
            SELECT
                id_producto,
                MAX(nombre_producto) AS nombre,
                SUM(unidades)        AS unidades,
                CASE WHEN SUM(ingreso) > 0
                     THEN SUM(margen) / SUM(ingreso) * 100
                END AS margen_pct
            FROM bi.kpi_producto_dia
            WHERE fecha >= :mes
              AND fecha < :mes + INTERVAL '1 month'
            GROUP BY id_producto
        )
        INSERT INTO bi.resumen_mensual_senal_precio
            (mes, id_producto, nombre,
             unidades, margen_pct, revisar_precio)
        SELECT
            :mes,
            id_producto,
            nombre,
            unidades,
            margen_pct,
            COALESCE(
                margen_pct <= (
                    SELECT PERCENTILE_CONT(0.25)
                           WITHIN GROUP (ORDER BY margen_pct)
                    FROM base WHERE margen_pct IS NOT NULL
                )
                AND unidades >= (
                    SELECT PERCENTILE_CONT(0.50)
                           WITHIN GROUP (ORDER BY unidades)
                    FROM base
                ),
                FALSE
            )
        FROM base
    """),
        params,
    )

    # ── M5: resumen_mensual_warning_insumo ────────────────────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_warning_insumo WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        WITH consumo_mes AS (
            SELECT
                id_insumo,
                id_producto,
                SUM(consumo) AS consumo_producto
            FROM bi.kpi_consumo_insumo_producto_dia
            WHERE fecha >= :mes
              AND fecha < :mes + INTERVAL '1 month'
            GROUP BY id_insumo, id_producto
        ),
        totales AS (
            SELECT
                id_insumo,
                SUM(consumo_producto)       AS consumo_total,
                COUNT(DISTINCT id_producto) AS num_productos_que_usan
            FROM consumo_mes
            GROUP BY id_insumo
        ),
        ranking AS (
            SELECT
                id_producto,
                MAX(nombre_producto) AS nombre,
                CASE WHEN SUM(ingreso) > 0
                     THEN SUM(margen) / SUM(ingreso) * 100
                END AS margen_pct
            FROM bi.kpi_producto_dia
            WHERE fecha >= :mes
              AND fecha < :mes + INTERVAL '1 month'
            GROUP BY id_producto
        ),
        umbral AS (
            SELECT PERCENTILE_CONT(0.25)
                   WITHIN GROUP (ORDER BY margen_pct) AS valor
            FROM ranking
            WHERE margen_pct IS NOT NULL
        )
        INSERT INTO bi.resumen_mensual_warning_insumo
            (mes, id_producto, id_insumo,
             nombre_producto, nombre_insumo,
             consumo_producto, consumo_total,
             pct_consumo_del_insumo,
             margen_pct, num_productos_que_usan, alerta)
        SELECT
            :mes,
            c.id_producto,
            c.id_insumo,
            r.nombre,
            i.nombre,
            c.consumo_producto,
            t.consumo_total,
            c.consumo_producto
                / NULLIF(t.consumo_total, 0) * 100,
            r.margen_pct,
            t.num_productos_que_usan,
            COALESCE(
                r.margen_pct <= (SELECT valor FROM umbral)
                AND t.num_productos_que_usan >= 2
                AND (c.consumo_producto
                     / NULLIF(t.consumo_total, 0)) >= 0.30,
                FALSE
            )
        FROM consumo_mes c
        JOIN totales t  ON t.id_insumo = c.id_insumo
        JOIN ranking r  ON r.id_producto = c.id_producto
        JOIN pos.insumo i ON i.id_insumo = c.id_insumo
    """),
        params,
    )

    # ── M6: resumen_mensual_insumo (fugas — C3 corregido) ────────────
    await db.execute(
        text("DELETE FROM bi.resumen_mensual_insumo WHERE mes = :mes"), params
    )
    await db.execute(
        text("""
        WITH base AS (
            SELECT
                k.id_insumo,
                MAX(k.nombre_insumo) AS nombre,
                SUM(k.consumo_neto) AS consumo_neto,
                SUM(k.merma_registrada) AS merma_registrada,
                SUM(k.consumo_neto * k.precio_real)
                    AS valor_consumo,
                CASE
                    WHEN SUM(
                        CASE WHEN k.consumo_neto > 0
                                  AND k.pct_rendimiento > 0
                             THEN k.consumo_neto
                        END
                    ) > 0
                    THEN SUM(
                        CASE WHEN k.consumo_neto > 0
                                  AND k.pct_rendimiento > 0
                             THEN k.pct_rendimiento * k.consumo_neto
                        END
                    ) / SUM(
                        CASE WHEN k.consumo_neto > 0
                                  AND k.pct_rendimiento > 0
                             THEN k.consumo_neto
                        END
                    )
                    ELSE 1.0
                END AS pct_teorico
            FROM bi.kpi_insumo_dia k
            WHERE k.fecha >= :mes
              AND k.fecha < :mes + INTERVAL '1 month'
            GROUP BY k.id_insumo
        ),
        calc AS (
            SELECT
                b.id_insumo,
                b.nombre,
                b.consumo_neto,
                b.merma_registrada,
                b.valor_consumo,
                b.consumo_neto AS cantidad,
                b.pct_teorico,
                CASE WHEN b.pct_teorico > 0
                     THEN b.consumo_neto
                          * (1.0 / b.pct_teorico - 1.0)
                     ELSE 0
                END AS merma_esperada,
                CASE WHEN (b.consumo_neto
                           + b.merma_registrada) > 0
                     THEN b.consumo_neto::numeric
                          / (b.consumo_neto
                             + b.merma_registrada)
                     ELSE 1.0
                END AS rendimiento_real,
                CASE WHEN b.consumo_neto > 0
                     THEN b.valor_consumo / b.consumo_neto
                     ELSE 0
                END AS avg_precio
            FROM base b
        )
        INSERT INTO bi.resumen_mensual_insumo
            (mes, id_insumo, nombre, unidad,
             consumo_neto, valor_consumo, cantidad,
             merma_registrada, merma_esperada,
             pct_rendimiento_teorico, rendimiento_real, brecha,
             costo_merma, costo_fuga, alerta_fuga)
        SELECT
            :mes,
            c.id_insumo,
            c.nombre,
            COALESCE(um.nombre, ''),
            c.consumo_neto,
            c.valor_consumo,
            c.cantidad,
            c.merma_registrada,
            c.merma_esperada,
            c.pct_teorico,
            c.rendimiento_real,
            c.pct_teorico - c.rendimiento_real,
            c.merma_registrada * c.avg_precio,
            GREATEST(
                c.merma_registrada - c.merma_esperada, 0
            ) * c.avg_precio,
            (c.pct_teorico - c.rendimiento_real) > 0.05
        FROM calc c
        LEFT JOIN pos.insumo i
            ON i.id_insumo = c.id_insumo
        LEFT JOIN pos.unidad_medida um
            ON um.id_unidad_medida = i.id_unidad_medida
    """),
        params,
    )


async def _paso6_notify_vercel() -> None:
    """Send cache purge webhook to Vercel after ETL completes.

    Best-effort: logs warning on failure but does not raise.
    The cache expires on its own TTL if the webhook fails.
    """
    url = settings.VERCEL_REVALIDATE_URL
    secret = settings.REVALIDATE_SECRET

    if url == "not-configured":
        logger.info("Vercel revalidate URL not configured — skipping webhook.")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers={"x-secret": secret},
            )
            response.raise_for_status()
            logger.info("Vercel cache purged successfully.")
    except Exception as exc:
        logger.warning("Vercel cache purge failed (best-effort): %s", exc)


async def procesar_dia(fecha: date, db: AsyncSession) -> None:
    """Run the full BI ETL pipeline for a given business day.

    Processes all KPI fact tables and rebuilds all summary tables.
    All steps run inside a single database transaction. On failure,
    the transaction is rolled back and the error is re-raised.

    Args:
        fecha: The Colombia local date to process (usually yesterday).
        db: Async SQLAlchemy session (transaction managed here).

    Raises:
        Exception: Re-raises any database or processing error after rollback.
    """
    v_ini, v_fin = _ventana_utc(fecha)
    logger.info(
        "Starting BI ETL for date %s (UTC window: %s → %s)",
        fecha,
        v_ini,
        v_fin,
    )

    try:
        await _paso1_kpi_producto_dia(db, fecha, v_ini, v_fin)
        logger.info("Step 1/6 complete: kpi_producto_dia")

        await _paso2_kpi_venta_hora_dia(db, fecha, v_ini, v_fin)
        logger.info("Step 2/6 complete: kpi_venta_hora_dia")

        await _paso3_kpi_insumo_dia(db, fecha, v_ini, v_fin)
        logger.info("Step 3/6 complete: kpi_insumo_dia")

        await _paso4_kpi_consumo_insumo_producto(db, fecha, v_ini, v_fin)
        logger.info("Step 4/6 complete: kpi_consumo_insumo_producto_dia")

        await _paso5_rebuild_resumenes(db, fecha)
        logger.info("Step 5/6 complete: all summary tables rebuilt")

        await db.commit()
        logger.info("BI ETL transaction committed for date %s", fecha)

    except Exception as exc:
        await db.rollback()
        logger.error("BI ETL failed for date %s: %s", fecha, exc)
        raise

    await _paso6_notify_vercel()
