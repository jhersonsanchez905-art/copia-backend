"""create bi schema fact and summary tables

Revision ID: 686e54a3d226
Revises: 2c4001937e5e
Create Date: 2026-06-11 10:14:18.594498
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "686e54a3d226"
down_revision = "2c4001937e5e"
branch_labels = None
depends_on = None

DDL_BI = """
-- ============================================================
-- BI Module · schema and tables · v1
-- Only schema created here: bi (pos and mkt already exist)
-- Only the ETL writes to bi.*; everything else is read-only.
-- No foreign keys to pos.* — intentional decoupling.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bi;

-- ── FACT TABLES ──────────────────────────────────────────────

CREATE TABLE bi.kpi_producto_dia (
    fecha            DATE    NOT NULL,
    id_producto      INT     NOT NULL,
    nombre_producto  TEXT,
    unidades         NUMERIC NOT NULL DEFAULT 0,
    ingreso          NUMERIC NOT NULL DEFAULT 0,
    costo            NUMERIC NOT NULL DEFAULT 0,
    margen           NUMERIC NOT NULL DEFAULT 0,
    margen_pct       NUMERIC,
    PRIMARY KEY (fecha, id_producto)
);

CREATE TABLE bi.kpi_venta_hora_dia (
    fecha       DATE     NOT NULL,
    hora        SMALLINT NOT NULL,
    dia_semana  SMALLINT NOT NULL,
    unidades    NUMERIC  NOT NULL DEFAULT 0,
    ingreso     NUMERIC  NOT NULL DEFAULT 0,
    PRIMARY KEY (fecha, hora)
);

CREATE TABLE bi.kpi_insumo_dia (
    fecha              DATE    NOT NULL,
    id_insumo          INT     NOT NULL,
    nombre_insumo      TEXT,
    stock_actual       NUMERIC,
    stock_minimo       NUMERIC,
    stock_maximo       NUMERIC,
    dias_anticipacion  INT,
    pct_rendimiento    NUMERIC,
    precio             NUMERIC,
    precio_real        NUMERIC,
    consumo_neto       NUMERIC NOT NULL DEFAULT 0,
    consumo_bruto      NUMERIC NOT NULL DEFAULT 0,
    PRIMARY KEY (fecha, id_insumo)
);

CREATE TABLE bi.kpi_consumo_insumo_producto_dia (
    fecha        DATE    NOT NULL,
    id_insumo    INT     NOT NULL,
    id_producto  INT     NOT NULL,
    consumo      NUMERIC NOT NULL DEFAULT 0,
    PRIMARY KEY (fecha, id_insumo, id_producto)
);

-- ── SUMMARY TABLES ───────────────────────────────────────────

CREATE TABLE bi.resumen_ranking_producto (
    id_producto      INT PRIMARY KEY,
    nombre_producto  TEXT,
    unidades         NUMERIC,
    margen_total     NUMERIC,
    margen_pct       NUMERIC
);

CREATE TABLE bi.resumen_heatmap_hora_dia (
    dia_semana     SMALLINT NOT NULL,
    hora           SMALLINT NOT NULL,
    unidades_prom  NUMERIC,
    ingreso_prom   NUMERIC,
    PRIMARY KEY (dia_semana, hora)
);

CREATE TABLE bi.resumen_recomendacion_compra (
    id_insumo             INT PRIMARY KEY,
    nombre_insumo         TEXT,
    stock_actual          NUMERIC,
    consumo_bruto_diario  NUMERIC,
    punto_pedido          NUMERIC,
    dispara_pedido        BOOLEAN,
    cantidad_a_comprar    NUMERIC
);

CREATE TABLE bi.resumen_senal_precio (
    id_producto      INT PRIMARY KEY,
    nombre_producto  TEXT,
    unidades         NUMERIC,
    margen_pct       NUMERIC,
    revisar_precio   BOOLEAN
);

CREATE TABLE bi.resumen_testeo_producto (
    id_producto      INT  NOT NULL,
    fecha            DATE NOT NULL,
    nombre_producto  TEXT,
    unidades         NUMERIC,
    margen           NUMERIC,
    PRIMARY KEY (id_producto, fecha)
);

CREATE TABLE bi.resumen_warning_insumo (
    id_producto             INT NOT NULL,
    id_insumo               INT NOT NULL,
    nombre_producto         TEXT,
    nombre_insumo           TEXT,
    consumo_producto        NUMERIC,
    consumo_total           NUMERIC,
    pct_consumo_del_insumo  NUMERIC,
    margen_pct              NUMERIC,
    num_productos_que_usan  INT,
    alerta                  BOOLEAN,
    PRIMARY KEY (id_producto, id_insumo)
);
"""


def upgrade() -> None:
    """Create bi schema with all fact and summary tables."""
    op.execute(DDL_BI)


def downgrade() -> None:
    """Drop bi schema and all its tables."""
    op.execute("DROP SCHEMA IF EXISTS bi CASCADE")