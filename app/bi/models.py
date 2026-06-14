"""Modelos espejo SQLAlchemy del esquema bi.

════════════════════════════════════════════════════════════════════════════════
TERRITORIO BI — NO MODIFICAR SIN COORDINACIÓN CON EL EQUIPO BI.
════════════════════════════════════════════════════════════════════════════════
Columnas y PKs idénticas al DDL congelado (bi_schema_v3.sql, SCRUM-6).

Propósito:
    Permitir que los endpoints GET de BI consulten las tablas ``bi.*``
    mediante SQLAlchemy (queries, ORM reads).

Notas de diseño:
    · ``__table_args__ = {"schema": "bi"}`` en  todos los modelos.
    · Sin relaciones hacia modelos ``pos.*`` — las referencias son lógicas.
    · Las únicas FKs son internas al esquema ``bi`` (auditoría ETL).
    · El esquema ``bi`` NO está en ``SCHEMAS`` de ``migrations/env.py``
      (Alembic lo ignora por diseño; la migración es manual).
    · Estos modelos NO definen relaciones ORM (solo columnas): los endpoints
      usan queries explícitas, no navegación lazy.

Ticket: SCRUM-21  ·  Dueño: Jherson  ·  Épica: SCRUM-6 BE-1
DDL fuente: bi_schema_v3.sql (congelado 2026-06-12, revisado por Stiven)
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.schema import ForeignKey, Index

from app.database import Base

_BI = {"schema": "bi"}


# ═════════════════════════════════════════════════════════════════════════════
# GRUPO 1 · HECHOS (4 tablas)
# Grano: día.  Operación ETL: upsert.  Semántica: append-only.
# ═════════════════════════════════════════════════════════════════════════════


class KpiProductoDia(Base):
    """[H-1] Ventas por producto y día."""

    __tablename__ = "kpi_producto_dia"
    __table_args__ = (
        *(),
        _BI,
    )

    fecha = Column(Date, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    nombre_producto = Column(Text)
    unidades = Column(Numeric, nullable=False, server_default=text("0"))
    ingreso = Column(Numeric, nullable=False, server_default=text("0"))
    costo = Column(Numeric, nullable=False, server_default=text("0"))
    margen = Column(Numeric, nullable=False, server_default=text("0"))
    margen_pct = Column(Numeric)


class KpiVentaHoraDia(Base):
    """[H-2] Ventas por hora y día (hora en America/Bogota)."""

    __tablename__ = "kpi_venta_hora_dia"
    __table_args__ = (
        *(),
        _BI,
    )

    fecha = Column(Date, primary_key=True, nullable=False)
    hora = Column(SmallInteger, primary_key=True, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)
    unidades = Column(Numeric, nullable=False, server_default=text("0"))
    ingreso = Column(Numeric, nullable=False, server_default=text("0"))
    num_ventas = Column(Integer, nullable=False, server_default=text("0"))


class KpiInsumoDia(Base):
    """[H-3] Consumo e inventario de insumos por día."""

    __tablename__ = "kpi_insumo_dia"
    __table_args__ = (
        *(),
        _BI,
    )

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
    consumo_neto = Column(Numeric, nullable=False, server_default=text("0"))
    consumo_bruto = Column(Numeric, nullable=False, server_default=text("0"))
    merma_registrada = Column(Numeric, nullable=False, server_default=text("0"))


class KpiConsumoInsumoProductoDia(Base):
    """[H-4] Consumo de insumo por producto y día."""

    __tablename__ = "kpi_consumo_insumo_producto_dia"
    __table_args__ = (
        *(),
        _BI,
    )

    fecha = Column(Date, primary_key=True, nullable=False)
    id_insumo = Column(Integer, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    consumo = Column(Numeric, nullable=False, server_default=text("0"))


# ═════════════════════════════════════════════════════════════════════════════
# GRUPO 2 · RESÚMENES DIARIOS (5 tablas)
# Foto de AYER.  Rebuild nocturno (DELETE + INSERT transaccional).
# ═════════════════════════════════════════════════════════════════════════════


class ResumenDiarioVentas(Base):
    """[D-1] KPIs de ventas de ayer + referencias mismo-día-semana ×4."""

    __tablename__ = "resumen_diario_ventas"
    __table_args__ = _BI

    fecha = Column(Date, primary_key=True)
    ingreso = Column(Numeric)
    unidades = Column(Numeric)
    num_pedidos = Column(Integer)
    promedio_venta_pedido = Column(Numeric)
    ref_ingreso = Column(Numeric)
    ref_unidades = Column(Numeric)
    ref_promedio_pedido = Column(Numeric)
    var_ingreso_pct = Column(Numeric)
    var_promedio_pedido_pct = Column(Numeric)
    merma_valor = Column(Numeric)
    actualizado_a = Column(TIMESTAMP(timezone=True))


class ResumenDiarioTopProducto(Base):
    """[D-2] Podio de productos (top 3 por unidades)."""

    __tablename__ = "resumen_diario_top_producto"
    __table_args__ = _BI

    posicion = Column(SmallInteger, primary_key=True)
    id_producto = Column(Integer)
    nombre = Column(Text)
    unidades = Column(Numeric)
    ingreso = Column(Numeric)


class ResumenDiarioTopInsumo(Base):
    """[D-3] Top insumos (top 5 por valor_consumo)."""

    __tablename__ = "resumen_diario_top_insumo"
    __table_args__ = _BI

    posicion = Column(SmallInteger, primary_key=True)
    id_insumo = Column(Integer)
    nombre = Column(Text)
    valor_consumo = Column(Numeric)
    cantidad = Column(Numeric)
    unidad = Column(Text)
    merma_valor = Column(Numeric)


class ResumenDiarioHoras(Base):
    """[D-4] Curva horaria de ayer vs patrón (mismo día semana, 90d)."""

    __tablename__ = "resumen_diario_horas"
    __table_args__ = _BI

    hora = Column(SmallInteger, primary_key=True)
    unidades = Column(Numeric)
    ingreso = Column(Numeric)
    patron_unidades = Column(Numeric)
    patron_ingreso = Column(Numeric)


class ResumenRecomendacionCompra(Base):
    """[D-5] Recomendación de compra (solo HOY, nunca histórico)."""

    __tablename__ = "resumen_recomendacion_compra"
    __table_args__ = _BI

    id_insumo = Column(Integer, primary_key=True)
    nombre_insumo = Column(Text)
    unidad = Column(Text)
    stock_actual = Column(Numeric)
    consumo_bruto_diario = Column(Numeric)
    punto_pedido = Column(Numeric)
    dispara_pedido = Column(Boolean)
    cantidad_a_comprar = Column(Numeric)


# ═════════════════════════════════════════════════════════════════════════════
# GRUPO 3 · RESÚMENES MENSUALES (6 tablas)
# Grano: mes calendario (DATE = día 1 del mes).
# ETL reescribe solo la fila del mes en curso; meses cerrados son inmutables.
# ═════════════════════════════════════════════════════════════════════════════


class ResumenMensualMeta(Base):
    """[M-1] Metadata de meses procesados."""

    __tablename__ = "resumen_mensual_meta"
    __table_args__ = _BI

    mes = Column(Date, primary_key=True)
    parcial = Column(Boolean, nullable=False)
    dias_con_datos = Column(SmallInteger)
    actualizado_a = Column(TIMESTAMP(timezone=True))


class ResumenMensualRanking(Base):
    """[M-2] Ranking mensual por producto (cantidad y ganancia bruta)."""

    __tablename__ = "resumen_mensual_ranking"
    __table_args__ = (
        *(),
        _BI,
    )

    mes = Column(Date, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(Text)
    unidades = Column(Numeric)
    ingreso = Column(Numeric)
    ganancia_bruta = Column(Numeric)
    margen_pct = Column(Numeric)


class ResumenMensualHeatmap(Base):
    """[M-3] Heatmap día×hora mensual (picos)."""

    __tablename__ = "resumen_mensual_heatmap"
    __table_args__ = (
        *(),
        _BI,
    )

    mes = Column(Date, primary_key=True, nullable=False)
    dia_semana = Column(SmallInteger, primary_key=True, nullable=False)
    hora = Column(SmallInteger, primary_key=True, nullable=False)
    unidades_prom = Column(Numeric)
    ingreso_prom = Column(Numeric)


class ResumenMensualSenalPrecio(Base):
    """[M-4] Señales de precio (productos con margen bajo y buen volumen)."""

    __tablename__ = "resumen_mensual_senal_precio"
    __table_args__ = (
        *(),
        _BI,
    )

    mes = Column(Date, primary_key=True, nullable=False)
    id_producto = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(Text)
    unidades = Column(Numeric)
    margen_pct = Column(Numeric)
    revisar_precio = Column(Boolean)


class ResumenMensualWarningInsumo(Base):
    """[M-5] Warnings de insumo compartido."""

    __tablename__ = "resumen_mensual_warning_insumo"
    __table_args__ = (
        *(),
        _BI,
    )

    mes = Column(Date, primary_key=True, nullable=False)
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


class ResumenMensualInsumo(Base):
    """[M-6] Top insumos del mes + fugas (rendimiento teórico vs real)."""

    __tablename__ = "resumen_mensual_insumo"
    __table_args__ = (
        *(),
        _BI,
    )

    mes = Column(Date, primary_key=True, nullable=False)
    id_insumo = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(Text)
    unidad = Column(Text)
    consumo_neto = Column(Numeric)
    valor_consumo = Column(Numeric)
    cantidad = Column(Numeric)
    merma_registrada = Column(Numeric)
    merma_esperada = Column(Numeric)
    pct_rendimiento_teorico = Column(Numeric)
    rendimiento_real = Column(Numeric)
    brecha = Column(Numeric)
    costo_merma = Column(Numeric)
    costo_fuga = Column(Numeric)
    alerta_fuga = Column(Boolean)


# ═════════════════════════════════════════════════════════════════════════════
# GRUPO 4 · AUDITORÍA DEL ETL (4 tablas)
# Bus de eventos de cada corrida.  FKs solo INTERNAS a bi.*.
# ═════════════════════════════════════════════════════════════════════════════


class EtlStatus(Base):
    """[A-1] Catálogo de estados de ejecución."""

    __tablename__ = "etl_status"
    __table_args__ = _BI

    id_status = Column(SmallInteger, primary_key=True)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)


class EtlStep(Base):
    """[A-2] Catálogo de pasos del ETL."""

    __tablename__ = "etl_step"
    __table_args__ = _BI

    id_step = Column(SmallInteger, primary_key=True)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    orden = Column(SmallInteger)


class EtlEjecucion(Base):
    """[A-3] Registro de corridas del ETL."""

    __tablename__ = "etl_ejecucion"
    __table_args__ = _BI

    id_ejecucion = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    fecha_procesada = Column(Date, nullable=False)
    origen = Column(Text, nullable=False)
    intento = Column(SmallInteger, nullable=False, server_default=text("1"))
    id_status = Column(
        SmallInteger,
        ForeignKey("bi.etl_status.id_status"),
        nullable=False,
    )
    inicio = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    fin = Column(TIMESTAMP(timezone=True))
    notificado_en = Column(TIMESTAMP(timezone=True))


class AuditEtl(Base):
    """[A-4] Bus de eventos por paso (audit log granular)."""

    __tablename__ = "audit_etl"
    __table_args__ = (
        Index("ix_audit_etl_ejecucion", "id_ejecucion"),
        _BI,
    )

    id_evento = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    id_ejecucion = Column(
        Integer,
        ForeignKey("bi.etl_ejecucion.id_ejecucion"),
        nullable=False,
    )
    id_step = Column(
        SmallInteger,
        ForeignKey("bi.etl_step.id_step"),
        nullable=False,
    )
    id_status = Column(
        SmallInteger,
        ForeignKey("bi.etl_status.id_status"),
        nullable=False,
    )
    descripcion = Column(Text)
    filas_afectadas = Column(Integer)
    duracion_ms = Column(Integer)
    fecha_evento = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
