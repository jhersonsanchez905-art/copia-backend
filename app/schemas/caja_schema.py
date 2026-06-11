"""
app/schemas/caja_schema.py

Pydantic schemas for cash register module request and response validation.

Author: Suley Suarez
Issue: #16
"""
from decimal import Decimal
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class TurnoEnum(str, Enum):
    manana = "manana"
    tarde = "tarde"


# ── Apertura Caja ─────────────────────────────────────────────────────────────

class AperturaCajaRequest(BaseModel):
    """Request schema to open a cash register shift."""
    turno: TurnoEnum
    fecha: date
    monto_inicial: Decimal
    observaciones: Optional[str] = None

    @field_validator("monto_inicial")
    @classmethod
    def monto_inicial_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El monto inicial no puede ser negativo")
        return v


class AperturaCajaResponse(BaseModel):
    """Cash register opening response."""
    id_apertura: int
    id_usuario: int
    turno: str
    fecha: date
    monto_inicial: Decimal
    hora_apertura: datetime
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ── Cierre Caja ───────────────────────────────────────────────────────────────

class CierreCajaDetalleRequest(BaseModel):
    """Payment method breakdown for cash register closing."""
    id_metodo_pago: int
    total_contado: Decimal

    @field_validator("total_contado")
    @classmethod
    def total_contado_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El monto contado no puede ser negativo")
        return v


class CierreCajaRequest(BaseModel):
    """Request schema to close a cash register shift."""
    observaciones: Optional[str] = None
    detalle: List[CierreCajaDetalleRequest]

    @model_validator(mode="after")
    def validar_detalle(self) -> "CierreCajaRequest":
        if not self.detalle:
            raise ValueError("Debe incluir al menos un detalle de cierre")
        ids = [d.id_metodo_pago for d in self.detalle]
        if len(ids) != len(set(ids)):
            raise ValueError("No se permiten métodos de pago duplicados en el mismo cierre")
        return self


class CierreCajaDetalleResponse(BaseModel):
    """Payment method detail in cash register closing response."""
    id_metodo_pago: int
    total_esperado: Decimal
    total_contado: Decimal
    diferencia: Decimal

    class Config:
        from_attributes = True


class CierreCajaResponse(BaseModel):
    """Cash register closing response."""
    id_cierre: int
    id_apertura: int
    id_usuario: int
    turno: str
    fecha: date
    total_general: Decimal
    total_transacciones: Decimal
    diferencia: Decimal
    hora_cierre: datetime
    observaciones: Optional[str] = None
    detalle: List[CierreCajaDetalleResponse] = []

    class Config:
        from_attributes = True
