"""BI module SQLAlchemy models for schema bi.

SQLAlchemy ORM models for the BI module (schema: bi).
Contains fact tables (kpi_*) and summary tables (resumen_*).

These models are intentionally decoupled from pos.* tables:
no foreign keys cross schema boundaries. This ensures the BI
historical record survives product/ingredient deletions in POS.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import Boolean, Column, Date, Integer, Numeric, SmallInteger, Text
from sqlalchemy.orm import DeclarativeBase


class BIBase(DeclarativeBase):
    """Base class for all BI module models."""

    pass


# ── FACT TABLES ───────────────────────────────────────────────────────────────
# Append-only with upsert. One row = one business entity per day.
# PKs are composite with `fecha` first for efficient date-range scans.


class KpiProductoDia(BIBase):
    """Daily sales KPI per product.

    Feeds: ranking, price signals, new product testing dashboards.
    Grain: one row per product per day.
    """

    __tablename__ = "kpi_producto_dia"
    __table_args__ = {"schema": "bi"}

    fecha = Column(Date, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    nombre_producto = Column(Text)
    unidades = Column(Numeric, nullable=False, default=0)
    ingreso = Column(Numeric, nullable=False, default=0)
    costo = Column(Numeric, nullable=False, default=0)
    margen = Column(Numeric, nullable=False, default=0)
    margen_pct = Column(Numeric)


class KpiVentaHoraDia(BIBase):
    """Hourly sales KPI per day (Colombia local time).

    Feeds: heatmap dashboard (peak hours analysis).
    Grain: one row per hour per day.
    """

    __tablename__ = "kpi_venta_hora_dia"
    __table_args__ = {"schema": "bi"}

    fecha = Column(Date, primary_key=True, nullable=False)
    hora = Column(SmallInteger, primary_key=True, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)
    unidades = Column(Numeric, nullable=False, default=0)
    ingreso = Column(Numeric, nullable=False, default=0)


class KpiInsumoDia(BIBase):
    """Daily ingredient snapshot: master data + consumption.

    Feeds: purchase recommendation dashboard.
    Grain: one row per ingredient per day.
    Note: stock_actual = pos.stock.cantidad (1:1 with insumo).
          precio_real = precio * 100 / pct_rendimiento (BI-calculated).
          pct_rendimiento stored as 0-100 scale (not 0-1).
    """

    __tablename__ = "kpi_insumo_dia"
    __table_args__ = {"schema": "bi"}

    fecha = Column(Date, primary_key=True, nullable=False)
    id_insumo = Column(Integer, primary_key=True, nullable=False)
    nombre_insumo = Column(Text)
    stock_actual = Column(Numeric)
    stock_minimo = Column(Numeric)
    stock_maximo = Column(Numeric)
    dias_anticipacion = Column(Integer)
    pct_rendimiento = Column(Numeric)
    precio = Column(Numeric)
    precio_real = Column(Numeric)
    consumo_neto = Column(Numeric, nullable=False, default=0)
    consumo_bruto = Column(Numeric, nullable=False, default=0)


class KpiConsumoInsumProductoDia(BIBase):
    """Daily ingredient consumption broken down by product.

    Feeds: shared ingredient warning dashboard.
    Grain: one row per ingredient per product per day.
    """

    __tablename__ = "kpi_consumo_insumo_producto_dia"
    __table_args__ = {"schema": "bi"}

    fecha = Column(Date, primary_key=True, nullable=False)
    id_insumo = Column(Integer, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    consumo = Column(Numeric, nullable=False, default=0)


# ── SUMMARY TABLES ────────────────────────────────────────────────────────────
# Rebuilt nightly by the ETL via DELETE + INSERT inside a transaction.
# These are what the GET endpoints read. Never written by anything else.


class ResumenRankingProducto(BIBase):
    """Product ranking summary for the last 30 days.

    Source: kpi_producto_dia (30-day window).
    """

    __tablename__ = "resumen_ranking_producto"
    __table_args__ = {"schema": "bi"}

    id_producto = Column(Integer, primary_key=True)
    nombre_producto = Column(Text)
    unidades = Column(Numeric)
    margen_total = Column(Numeric)
    margen_pct = Column(Numeric)


class ResumenHeatmapHoraDia(BIBase):
    """Average hourly sales heatmap for the last 90 days.

    Source: kpi_venta_hora_dia (90-day window).
    """

    __tablename__ = "resumen_heatmap_hora_dia"
    __table_args__ = {"schema": "bi"}

    dia_semana = Column(SmallInteger, primary_key=True, nullable=False)
    hora = Column(SmallInteger, primary_key=True, nullable=False)
    unidades_prom = Column(Numeric)
    ingreso_prom = Column(Numeric)


class ResumenRecomendacionCompra(BIBase):
    """Purchase recommendation per ingredient.

    Source: kpi_insumo_dia (28-day window) + live pos.stock.
    Formula: punto_pedido = daily_rate * dias_anticipacion + stock_minimo.
             cantidad_a_comprar = GREATEST(daily_rate * 7 * 1.20 - stock, 0).
    """

    __tablename__ = "resumen_recomendacion_compra"
    __table_args__ = {"schema": "bi"}

    id_insumo = Column(Integer, primary_key=True)
    nombre_insumo = Column(Text)
    stock_actual = Column(Numeric)
    consumo_bruto_diario = Column(Numeric)
    punto_pedido = Column(Numeric)
    dispara_pedido = Column(Boolean)
    cantidad_a_comprar = Column(Numeric)


class ResumenSenalPrecio(BIBase):
    """Price signal: products with margin below P25 and volume above P50.

    Source: kpi_producto_dia (30-day window).
    """

    __tablename__ = "resumen_senal_precio"
    __table_args__ = {"schema": "bi"}

    id_producto = Column(Integer, primary_key=True)
    nombre_producto = Column(Text)
    unidades = Column(Numeric)
    margen_pct = Column(Numeric)
    revisar_precio = Column(Boolean)


class ResumenTesteoProducto(BIBase):
    """Daily performance series for recently launched products (last 60 days).

    Source: kpi_producto_dia JOIN pos.producto (fecha_lanzamiento).
    """

    __tablename__ = "resumen_testeo_producto"
    __table_args__ = {"schema": "bi"}

    id_producto = Column(Integer, primary_key=True, nullable=False)
    fecha = Column(Date, primary_key=True, nullable=False)
    nombre_producto = Column(Text)
    unidades = Column(Numeric)
    margen = Column(Numeric)


class ResumenWarningInsumo(BIBase):
    """Shared ingredient warning: low-margin products consuming a large share.

    Source: kpi_consumo_insumo_producto_dia (30-day window) + resumen_ranking.
    Alert fires when: margin <= P25 AND product uses >= 30% of a shared ingredient.
    """

    __tablename__ = "resumen_warning_insumo"
    __table_args__ = {"schema": "bi"}

    id_producto = Column(Integer, primary_key=True, nullable=False)
    id_insumo = Column(Integer, primary_key=True, nullable=False)
    nombre_producto = Column(Text)
    nombre_insumo = Column(Text)
    consumo_producto = Column(Numeric)
    consumo_total = Column(Numeric)
    pct_consumo_del_insumo = Column(Numeric)
    margen_pct = Column(Numeric)
    num_productos_que_usan = Column(Integer)
    alerta = Column(Boolean)
