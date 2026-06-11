"""BI module Pydantic schemas for API request and response validation.

Defines the JSON contract between the BI endpoints and the frontend.
All response models map 1:1 to their corresponding bi.resumen_* table.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class RankingProductoSchema(BaseModel):
    """Response schema for GET /bi/ranking-productos."""

    id_producto: int
    nombre_producto: str | None
    unidades: Decimal | None
    margen_total: Decimal | None
    margen_pct: Decimal | None

    model_config = {"from_attributes": True}


class HeatmapHoraDiaSchema(BaseModel):
    """Response schema for GET /bi/heatmap."""

    dia_semana: int
    hora: int
    unidades_prom: Decimal | None
    ingreso_prom: Decimal | None

    model_config = {"from_attributes": True}


class RecomendacionCompraSchema(BaseModel):
    """Response schema for GET /bi/recomendacion-compra."""

    id_insumo: int
    nombre_insumo: str | None
    stock_actual: Decimal | None
    consumo_bruto_diario: Decimal | None
    punto_pedido: Decimal | None
    dispara_pedido: bool | None
    cantidad_a_comprar: Decimal | None

    model_config = {"from_attributes": True}


class SenalPrecioSchema(BaseModel):
    """Response schema for GET /bi/senales-precio."""

    id_producto: int
    nombre_producto: str | None
    unidades: Decimal | None
    margen_pct: Decimal | None
    revisar_precio: bool | None

    model_config = {"from_attributes": True}


class TesteoProductoSchema(BaseModel):
    """Response schema for GET /bi/testeo-productos."""

    id_producto: int
    fecha: date
    nombre_producto: str | None
    unidades: Decimal | None
    margen: Decimal | None

    model_config = {"from_attributes": True}


class WarningInsumoSchema(BaseModel):
    """Response schema for GET /bi/warnings-insumo."""

    id_producto: int
    id_insumo: int
    nombre_producto: str | None
    nombre_insumo: str | None
    consumo_producto: Decimal | None
    consumo_total: Decimal | None
    pct_consumo_del_insumo: Decimal | None
    margen_pct: Decimal | None
    num_productos_que_usan: int | None
    alerta: bool | None

    model_config = {"from_attributes": True}


class ProcesarDiaRequest(BaseModel):
    """Request schema for POST /bi/procesar-dia."""

    fecha: date | None = None


class ProcesarDiaResponse(BaseModel):
    """Response schema for POST /bi/procesar-dia."""

    ok: bool
    fecha_procesada: date
    duracion_ms: int
