"""
insumo_schema.py
Pydantic schemas for Insumo, Subreceta, and SubrecetaIngrediente.
Fields match model columns exactly.
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Insumo ────────────────────────────────────────────────────────────────────

class InsumoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    presentacion: Optional[str] = Field(None, max_length=120)
    id_unidad: int
    id_clasificacion: int
    id_marca: Optional[int] = None
    contador_unidades: Optional[int] = None
    precio: Optional[Decimal] = None
    pct_rendimiento: Optional[Decimal] = None
    umbral_minimo: Decimal = Decimal("0")
    stock_minimo: Decimal = Decimal("0")
    stock_maximo: Optional[Decimal] = None
    punto_pedido: Optional[Decimal] = None
    cantidad_a_pedir: Optional[Decimal] = None
    dias_anticipacion: Optional[int] = None
    activo: bool = True


class InsumoCreate(InsumoBase):
    pass


class InsumoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    presentacion: Optional[str] = None
    id_unidad: Optional[int] = None
    id_clasificacion: Optional[int] = None
    id_marca: Optional[int] = None
    contador_unidades: Optional[int] = None
    precio: Optional[Decimal] = None
    pct_rendimiento: Optional[Decimal] = None
    umbral_minimo: Optional[Decimal] = None
    stock_minimo: Optional[Decimal] = None
    stock_maximo: Optional[Decimal] = None
    punto_pedido: Optional[Decimal] = None
    cantidad_a_pedir: Optional[Decimal] = None
    dias_anticipacion: Optional[int] = None
    activo: Optional[bool] = None


class InsumoResponse(InsumoBase):
    model_config = ConfigDict(from_attributes=True)

    id_insumo: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime


# ── Subreceta ─────────────────────────────────────────────────────────────────

class SubrecetaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    porciones: Optional[int] = None
    peso_porcion_gr: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    activo: bool = True


class SubrecetaCreate(SubrecetaBase):
    pass


class SubrecetaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    porciones: Optional[int] = None
    peso_porcion_gr: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    activo: Optional[bool] = None


class SubrecetaResponse(SubrecetaBase):
    model_config = ConfigDict(from_attributes=True)

    id_subreceta: int


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

class SubrecetaIngredienteBase(BaseModel):
    id_subreceta: int
    id_insumo: int
    id_unidad: int
    cantidad: Decimal = Field(..., gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class SubrecetaIngredienteCreate(SubrecetaIngredienteBase):
    pass


class SubrecetaIngredienteUpdate(BaseModel):
    id_unidad: Optional[int] = None
    cantidad: Optional[Decimal] = Field(None, gt=0)
    costo_unitario: Optional[Decimal] = None
    costo_total: Optional[Decimal] = None
    pct_participacion: Optional[Decimal] = None


class SubrecetaIngredienteResponse(SubrecetaIngredienteBase):
    model_config = ConfigDict(from_attributes=True)

    id_subreceta_ing: int
