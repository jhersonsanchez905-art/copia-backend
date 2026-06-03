"""
insumo_schema.py
Schemas Pydantic para validación y serialización de insumos, subrecetas e ingredientes de subreceta.
Autor: Ivan Ospino
Issue: #19
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ── Insumo ────────────────────────────────────────────────────────────────────

class InsumoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    unidad_medida: str
    stock_actual: Optional[Decimal] = Decimal("0")
    umbral_minimo: Optional[Decimal] = Decimal("0")
    costo_unitario: Optional[Decimal] = None
    activo: Optional[bool] = True


class InsumoCreate(InsumoBase):
    pass


class InsumoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    stock_actual: Optional[Decimal] = None
    umbral_minimo: Optional[Decimal] = None
    costo_unitario: Optional[Decimal] = None
    activo: Optional[bool] = None


class InsumoOut(InsumoBase):
    id_insumo: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ── Subreceta ─────────────────────────────────────────────────────────────────

class SubrecetaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    rendimiento: Optional[Decimal] = Decimal("1")
    unidad_rendimiento: Optional[str] = "porcion"
    activo: Optional[bool] = True


class SubrecetaCreate(SubrecetaBase):
    pass


class SubrecetaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    rendimiento: Optional[Decimal] = None
    unidad_rendimiento: Optional[str] = None
    activo: Optional[bool] = None


class SubrecetaOut(SubrecetaBase):
    id_subreceta: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

class SubrecetaIngredienteBase(BaseModel):
    id_subreceta: int
    id_insumo: int
    cantidad: Decimal


class SubrecetaIngredienteCreate(SubrecetaIngredienteBase):
    pass


class SubrecetaIngredienteUpdate(BaseModel):
    cantidad: Decimal


class SubrecetaIngredienteOut(SubrecetaIngredienteBase):
    fecha_creacion: datetime

    class Config:
        from_attributes = True