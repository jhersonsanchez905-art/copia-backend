"""
caja_schema.py
Pydantic schemas for cash register module: apertura, cierre, and cierre detalle.

Author: Suley Suarez / Jherson
Issue: #16, #40
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TurnoEnum(str, Enum):
    manana = "manana"
    tarde = "tarde"


# ── Apertura Caja ─────────────────────────────────────────────────────────────

class AperturaCajaRequest(BaseModel):
    turno: TurnoEnum
    fecha: date
    monto_inicial: Decimal
    observaciones: Optional[str] = None


class AperturaCajaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_apertura: int
    id_usuario: int
    turno: str
    fecha: date
    monto_inicial: Decimal
    hora_apertura: datetime
    observaciones: Optional[str] = None


# ── Cierre Caja ───────────────────────────────────────────────────────────────

class CierreCajaDetalleRequest(BaseModel):
    id_metodo_pago: int
    total_contado: Decimal


class CierreCajaRequest(BaseModel):
    observaciones: Optional[str] = None
    detalle: List[CierreCajaDetalleRequest]


class CierreCajaDetalleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_detalle: int
    id_metodo_pago: int
    total_esperado: Decimal
    total_contado: Decimal
    diferencia: Decimal


class CierreCajaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    detalles: List[CierreCajaDetalleResponse] = []
