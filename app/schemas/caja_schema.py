"""
app/schemas/caja_schema.py

Pydantic schemas for cash register module request and response validation.

Author: Suley Suarez
Issue: #16
"""
from pydantic import BaseModel
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
    monto_inicial: float
    observaciones: Optional[str] = None


class AperturaCajaResponse(BaseModel):
    """Cash register opening response."""
    id_apertura: int
    id_usuario: int
    turno: str
    fecha: date
    monto_inicial: float
    hora_apertura: datetime
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


# ── Cierre Caja ───────────────────────────────────────────────────────────────

class CierreCajaDetalleRequest(BaseModel):
    """Payment method breakdown for cash register closing."""
    id_metodo_pago: int
    total_contado: float


class CierreCajaRequest(BaseModel):
    """Request schema to close a cash register shift."""
    observaciones: Optional[str] = None
    detalle: List[CierreCajaDetalleRequest]


class CierreCajaDetalleResponse(BaseModel):
    """Payment method detail in cash register closing response."""
    id_metodo_pago: int
    total_esperado: float
    total_contado: float
    diferencia: float

    class Config:
        from_attributes = True


class CierreCajaResponse(BaseModel):
    """Cash register closing response."""
    id_cierre: int
    id_apertura: int
    id_usuario: int
    turno: str
    fecha: date
    total_general: float
    total_transacciones: float
    diferencia: float
    hora_cierre: datetime
    observaciones: Optional[str] = None
    detalle: List[CierreCajaDetalleResponse] = []

    class Config:
        from_attributes = True
