"""BI module Pydantic schemas for API request and response validation.

Defines the JSON contract between the BI endpoints and the frontend,
per documento_canonico §4 (Contrato de datos v3).

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════════
# Dashboard diario (§4.1) — GET /bi/dashboard/diario, GET /bi/diario
# ═══════════════════════════════════════════════════════════════════


class ReferenciaVentasSchema(BaseModel):
    """Reference values: same weekday average of the 4 previous weeks."""

    tipo: str = "mismo_dia_semana_x4"
    ingreso: Decimal | None
    unidades: Decimal | None = None
    promedio_venta_pedido: Decimal | None


class VariacionVentasSchema(BaseModel):
    """Percentage variation vs. the reference."""

    ingreso_pct: Decimal | None
    promedio_venta_pedido_pct: Decimal | None


class VentasDiariasSchema(BaseModel):
    """ventas block of the daily dashboard."""

    ingreso: Decimal
    unidades: Decimal
    num_pedidos: int
    promedio_venta_pedido: Decimal | None
    referencia: ReferenciaVentasSchema
    variacion: VariacionVentasSchema


class MermaSchema(BaseModel):
    """merma block of the daily dashboard."""

    valor: Decimal


class TopProductoSchema(BaseModel):
    """Single entry in top_productos (podium, 1-3)."""

    posicion: int
    id_producto: int
    nombre: str | None
    unidades: Decimal
    ingreso: Decimal

    model_config = {"from_attributes": True}


class TopInsumoSchema(BaseModel):
    """Single entry in top_insumos (1-5, ordered by valor_consumo)."""

    posicion: int
    id_insumo: int
    nombre: str | None
    valor_consumo: Decimal | None
    cantidad: Decimal | None
    unidad: str | None
    merma_valor: Decimal | None

    model_config = {"from_attributes": True}


class VentaHoraSchema(BaseModel):
    """Single hour entry in ventas_por_hora."""

    hora: int
    unidades: Decimal | None
    ingreso: Decimal | None
    patron_unidades: Decimal | None
    patron_ingreso: Decimal | None

    model_config = {"from_attributes": True}


class RecomendacionCompraSchema(BaseModel):
    """Single entry in recomendacion_compra."""

    id_insumo: int
    nombre: str | None
    unidad: str | None
    stock_actual: Decimal | None
    consumo_bruto_diario: Decimal | None
    punto_pedido: Decimal | None
    dispara_pedido: bool | None
    cantidad_a_comprar: Decimal | None

    model_config = {"from_attributes": True}


class DashboardDiarioSchema(BaseModel):
    """Response schema for GET /bi/dashboard/diario and GET /bi/diario.

    /bi/diario (B puntual) omits recomendacion_compra — see §4.2.
    """

    fecha_analisis: date
    actualizado_a: datetime
    ventas: VentasDiariasSchema
    merma: MermaSchema
    top_productos: list[TopProductoSchema]
    top_insumos: list[TopInsumoSchema]
    ventas_por_hora: list[VentaHoraSchema]
    recomendacion_compra: list[RecomendacionCompraSchema] | None = None


# ═══════════════════════════════════════════════════════════════════
# Dashboard mensual (§4.1) — GET /bi/dashboard/mensual, GET /bi/mensual
# ═══════════════════════════════════════════════════════════════════


class RankingCantidadSchema(BaseModel):
    """Single entry in ranking_cantidad (resumen_mensual_ranking)."""

    id_producto: int
    nombre: str | None
    unidades: Decimal | None
    ingreso: Decimal | None

    model_config = {"from_attributes": True}


class GananciaBrutaSchema(BaseModel):
    """Single entry in ganancia_bruta (resumen_mensual_ranking)."""

    id_producto: int
    nombre: str | None
    ganancia_bruta: Decimal | None
    margen_pct: Decimal | None
    unidades: Decimal | None

    model_config = {"from_attributes": True}


class TopProductoMesSchema(BaseModel):
    """top_producto block — single product, highest unidades of the month."""

    id_producto: int
    nombre: str | None
    unidades: Decimal | None


class TopInsumoMesSchema(BaseModel):
    """top_insumo block — single ingredient, highest valor_consumo."""

    id_insumo: int
    nombre: str | None
    valor_consumo: Decimal | None
    cantidad: Decimal | None
    unidad: str | None


class PicoHoraSchema(BaseModel):
    """Single entry in picos (resumen_mensual_heatmap)."""

    dia_semana: int
    hora: int
    unidades_prom: Decimal | None
    ingreso_prom: Decimal | None

    model_config = {"from_attributes": True}


class SenalPrecioSchema(BaseModel):
    """Single entry in senales_precio (resumen_mensual_senal_precio)."""

    id_producto: int
    nombre: str | None
    margen_pct: Decimal | None
    unidades: Decimal | None
    revisar_precio: bool | None

    model_config = {"from_attributes": True}


class WarningInsumoSchema(BaseModel):
    """Single entry in warnings_insumo (resumen_mensual_warning_insumo)."""

    id_producto: int
    id_insumo: int
    nombre_producto: str | None
    nombre_insumo: str | None
    pct_consumo_del_insumo: Decimal | None
    margen_pct: Decimal | None
    num_productos_que_usan: int | None
    alerta: bool | None

    model_config = {"from_attributes": True}


class FugaInsumoSchema(BaseModel):
    """Single entry in fugas (resumen_mensual_insumo).

    En evaluación — el front puede ocultar la sección con un flag (§4.1).
    """

    id_insumo: int
    nombre: str | None
    pct_rendimiento_teorico: Decimal | None
    rendimiento_real: Decimal | None
    brecha: Decimal | None
    costo_fuga: Decimal | None
    alerta_fuga: bool | None

    model_config = {"from_attributes": True}


class DashboardMensualSchema(BaseModel):
    """Response schema for GET /bi/dashboard/mensual and GET /bi/mensual.

    /bi/mensual (B puntual) omits mes_anterior — see §4.2.
    """

    mes: str
    parcial: bool
    dias_con_datos: int | None
    actualizado_a: datetime
    ranking_cantidad: list[RankingCantidadSchema]
    ganancia_bruta: list[GananciaBrutaSchema]
    top_producto: TopProductoMesSchema | None
    top_insumo: TopInsumoMesSchema | None
    picos: list[PicoHoraSchema]
    senales_precio: list[SenalPrecioSchema]
    warnings_insumo: list[WarningInsumoSchema]
    fugas: list[FugaInsumoSchema]
    mes_anterior: "DashboardMensualSchema | None" = None


# ═══════════════════════════════════════════════════════════════════
# Explorar — rangos (§4.2)
# ═══════════════════════════════════════════════════════════════════


class VariacionRangoDiarioSchema(BaseModel):
    """variacion block for GET /bi/diario/comparar (case A)."""

    ingreso_pct: Decimal | None
    unidades_pct: Decimal | None
    promedio_venta_pedido_pct: Decimal | None


class ComparacionDiariaSchema(BaseModel):
    """Response schema for GET /bi/diario/comparar (case A diario)."""

    a: DashboardDiarioSchema
    b: DashboardDiarioSchema
    variacion: VariacionRangoDiarioSchema


class RangoDiarioSchema(DashboardDiarioSchema):
    """Response schema for GET /bi/diario/rango (case C diario).

    Same shape as the daily dashboard, plus dias_incluidos. Tops and
    the hourly curve are aggregated over the full range.
    """

    dias_incluidos: int


class VariacionRangoMensualSchema(BaseModel):
    """variacion block for GET /bi/mensual/comparar (case A)."""

    ingreso_pct: Decimal | None
    unidades_pct: Decimal | None
    margen_pct_diff: Decimal | None = None


class ComparacionMensualSchema(BaseModel):
    """Response schema for GET /bi/mensual/comparar (case A mensual)."""

    a: DashboardMensualSchema
    b: DashboardMensualSchema
    variacion: VariacionRangoMensualSchema


class RangoMensualSchema(DashboardMensualSchema):
    """Response schema for GET /bi/mensual/rango (case C mensual)."""

    meses_incluidos: int


# ═══════════════════════════════════════════════════════════════════
# Meta (§4.2) — GET /bi/meta
# ═══════════════════════════════════════════════════════════════════


class MetaSchema(BaseModel):
    """Response schema for GET /bi/meta.

    Used by the front to bound date-range selectors.
    """

    historico_desde: date
    ultimo_dia_procesado: date


# ═══════════════════════════════════════════════════════════════════
# Funcionalidades (§4.3)
# ═══════════════════════════════════════════════════════════════════


class ProductoBusquedaSchema(BaseModel):
    """Single entry for GET /bi/funcionalidades/productos?buscar=..."""

    id_producto: int
    nombre: str
    fecha_lanzamiento: date | None

    model_config = {"from_attributes": True}


class SerieTesteoSchema(BaseModel):
    """Single day entry in the testeo-producto series."""

    fecha: date
    unidades: Decimal | None
    ingreso: Decimal | None
    ganancia_bruta: Decimal | None

    model_config = {"from_attributes": True}


class RangoDisponibleSchema(BaseModel):
    """Available date range for a product's test series."""

    desde: date
    hasta: date


class TesteoProductoSchema(BaseModel):
    """Response schema for GET /bi/funcionalidades/testeo-producto/{id}.

    desde/hasta query params are optional (default: desde lanzamiento).
    Out-of-range dates return 422 with rango_disponible.
    A product with no recipe/sales returns an empty serie + rango_disponible.
    """

    id_producto: int
    nombre: str
    fecha_lanzamiento: date | None
    rango_disponible: RangoDisponibleSchema
    serie: list[SerieTesteoSchema]


class CampanaListaSchema(BaseModel):
    """Single entry for GET /bi/funcionalidades/campanas."""

    id_campana: int
    nombre: str
    estado: str
    fecha_inicio: date
    fecha_fin: date | None

    model_config = {"from_attributes": True}


class SerieCampanaSchema(BaseModel):
    """Single day entry in a campaign's comparison series."""

    fecha: date
    ingreso: Decimal | None
    periodo: str  # "baseline" | "campana"


class ProductoCampanaSchema(BaseModel):
    """Single product included in a campaign."""

    id_producto: int
    nombre: str
    descuento_pct: Decimal | None


class CampanaDetalleSchema(BaseModel):
    """Response schema for GET /bi/funcionalidades/campana/{id}.

    Presentar SIEMPRE como variación, nunca causalidad (§4.3).
    """

    id_campana: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date | None
    baseline_dias: int
    prom_diario_baseline: Decimal | None
    prom_diario_campana: Decimal | None
    variacion_pct: Decimal | None
    serie: list[SerieCampanaSchema]
    productos: list[ProductoCampanaSchema]


# ═══════════════════════════════════════════════════════════════════
# Operación (§4.4)
# ═══════════════════════════════════════════════════════════════════


class ProcesarDiaRequest(BaseModel):
    """Request schema for POST /bi/procesar-dia.

    fecha is optional — defaults to "yesterday" (Colombia local) if
    omitted. origen is set by the caller (cron sends X-Cron-Secret).
    """

    fecha: date | None = None


class ProcesarDiaResponse(BaseModel):
    """Response schema for POST /bi/procesar-dia."""

    ok: bool
    id_ejecucion: int
    fecha_procesada: date
    status: str


class EjecucionEtlSchema(BaseModel):
    """Single entry for GET /bi/admin/etl/ejecuciones (optional health panel)."""

    id_ejecucion: int
    fecha_procesada: date
    origen: str
    intento: int
    status: str
    inicio: datetime
    fin: datetime | None

    model_config = {"from_attributes": True}
