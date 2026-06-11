"""
receta_schema.py
Pydantic schemas for RecetaVersion, RecetaDetalleInsumo,
RecetaDetalleSubreceta, and RecetaPaso.
RecetaDetalle is split into two separate schemas matching the finalized models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ── RecetaPaso ──────────────────────────────────────────────────────────────

class RecetaPasoBase(BaseModel):
    numero_paso: int = Field(..., ge=1)
    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    tiempo_estimado_min: Optional[int] = Field(None, ge=0)


class RecetaPasoCreate(RecetaPasoBase):
    pass


class RecetaPasoUpdate(BaseModel):
    numero_paso: Optional[int] = Field(None, ge=1)
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = None
    tiempo_estimado_min: Optional[int] = Field(None, ge=0)


class RecetaPasoResponse(RecetaPasoBase):
    model_config = ConfigDict(from_attributes=True)

    id_paso: int
    id_receta_version: int


# ── RecetaDetalleInsumo ─────────────────────────────────────────────────────

class RecetaDetalleInsumoBase(BaseModel):
    id_insumo: int
    id_unidad: int
    cantidad: Decimal = Field(..., gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class RecetaDetalleInsumoCreate(RecetaDetalleInsumoBase):
    pass


class RecetaDetalleInsumoUpdate(BaseModel):
    id_insumo: Optional[int] = None
    id_unidad: Optional[int] = None
    cantidad: Optional[Decimal] = Field(None, gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class RecetaDetalleInsumoResponse(RecetaDetalleInsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id_receta_detalle_insumo: int
    id_receta_version: int


# ── RecetaDetalleSubreceta ──────────────────────────────────────────────────

class RecetaDetalleSubrecetaBase(BaseModel):
    id_subreceta: int
    id_unidad: int
    cantidad: Decimal = Field(..., gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class RecetaDetalleSubrecetaCreate(RecetaDetalleSubrecetaBase):
    pass


class RecetaDetalleSubrecetaUpdate(BaseModel):
    id_subreceta: Optional[int] = None
    id_unidad: Optional[int] = None
    cantidad: Optional[Decimal] = Field(None, gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class RecetaDetalleSubrecetaResponse(RecetaDetalleSubrecetaBase):
    model_config = ConfigDict(from_attributes=True)

    id_receta_detalle_subreceta: int
    id_receta_version: int


# ── RecetaVersion ───────────────────────────────────────────────────────────

class RecetaVersionBase(BaseModel):
    costo_total: Optional[Decimal] = None
    tiempo_preparacion_min: Optional[int] = Field(None, ge=0)
    instrucciones_generales: Optional[str] = None
    observaciones: Optional[str] = None


class RecetaVersionCreate(RecetaVersionBase):
    id_producto: int
    detalles_insumo: list[RecetaDetalleInsumoCreate] = Field(default_factory=list)
    detalles_subreceta: list[RecetaDetalleSubrecetaCreate] = Field(default_factory=list)
    pasos: list[RecetaPasoCreate] = Field(default_factory=list)


class RecetaVersionUpdate(RecetaVersionBase):
    pass


class RecetaVersionResponse(RecetaVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id_receta_version: int
    id_producto: int
    nombre_producto: Optional[str] = None
    version: int
    vigente: bool
    fecha_creacion: Optional[datetime] = None
    detalles_insumo: list[RecetaDetalleInsumoResponse] = []
    detalles_subreceta: list[RecetaDetalleSubrecetaResponse] = []
    pasos: list[RecetaPasoResponse] = []
