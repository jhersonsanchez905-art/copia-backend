"""
receta_schema.py
Esquemas Pydantic para el CRUD de RecetaVersion, RecetaDetalle y RecetaPaso.
Autor: SebastianValero12
Issue: #40
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# ── RecetaPaso ──────────────────────────────────────────────

class RecetaPasoBase(BaseModel):
    numero_paso: int = Field(..., ge=1)
    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: str | None = None
    tiempo_estimado_min: int | None = Field(None, ge=0)


class RecetaPasoCreate(RecetaPasoBase):
    """Se usa dentro de RecetaVersionCreate (sin id_receta_version)."""
    pass


class RecetaPasoUpdate(BaseModel):
    numero_paso: int | None = Field(None, ge=1)
    titulo: str | None = Field(None, min_length=1, max_length=200)
    descripcion: str | None = None
    tiempo_estimado_min: int | None = Field(None, ge=0)


class RecetaPasoResponse(RecetaPasoBase):
    model_config = ConfigDict(from_attributes=True)

    id_paso: int
    id_receta_version: int


# ── RecetaDetalle ───────────────────────────────────────────

class RecetaDetalleBase(BaseModel):
    id_insumo: int | None = None
    id_subreceta: int | None = None
    id_unidad: int
    cantidad: Decimal = Field(..., gt=0)
    costo_unitario: Decimal | None = None
    costo_total: Decimal | None = None
    pct_participacion: Decimal | None = None


class RecetaDetalleCreate(RecetaDetalleBase):
    """Se usa dentro de RecetaVersionCreate (sin id_receta_version)."""
    pass


class RecetaDetalleUpdate(BaseModel):
    id_insumo: int | None = None
    id_subreceta: int | None = None
    id_unidad: int | None = None
    cantidad: Decimal | None = Field(None, gt=0)
    costo_unitario: Decimal | None = None
    costo_total: Decimal | None = None
    pct_participacion: Decimal | None = None


class RecetaDetalleResponse(RecetaDetalleBase):
    model_config = ConfigDict(from_attributes=True)

    id_receta_detalle: int
    id_receta_version: int


# ── RecetaVersion ───────────────────────────────────────────

class RecetaVersionBase(BaseModel):
    costo_total: Decimal | None = None
    tiempo_preparacion_min: int | None = Field(None, ge=0)
    instrucciones_generales: str | None = None
    observaciones: str | None = None


class RecetaVersionCreate(RecetaVersionBase):
    """
    Crea una nueva versión de receta para un producto.
    El número de versión se calcula automáticamente.
    Los detalles y pasos se crean en cascada.
    """
    id_producto: int
    detalles: list[RecetaDetalleCreate] = Field(default_factory=list)
    pasos: list[RecetaPasoCreate] = Field(default_factory=list)


class RecetaVersionUpdate(RecetaVersionBase):
    """Solo actualiza metadatos de la versión (no detalles ni pasos)."""
    pass


class RecetaVersionResponse(RecetaVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id_receta_version: int
    id_producto: int
    version: int
    vigente: bool
    fecha_creacion: datetime | None = None
    detalles: list[RecetaDetalleResponse] = []
    pasos: list[RecetaPasoResponse] = []