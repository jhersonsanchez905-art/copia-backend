"""
app/schemas/inventario_schema.py

Pydantic schemas for inventory module request and response validation.

Author: Suley Suarez
Issue: #16
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoMovimientoEnum(str, Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"
    merma = "merma"


class EstadoAjusteEnum(str, Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


class SemaforoEnum(str, Enum):
    verde = "verde"
    amarillo = "amarillo"
    rojo = "rojo"


# ── Ajuste Manual ─────────────────────────────────────────────────────────────

class AjusteInventarioRequest(BaseModel):
    """Request schema for a manual inventory adjustment."""
    id_insumo: int
    cantidad: float
    motivo: str
    observacion: Optional[str] = None


class AjusteInventarioResponse(BaseModel):
    """Manual inventory adjustment response."""
    id_movimiento: int
    id_insumo: int
    tipo: str
    cantidad: float
    motivo: str
    observacion: Optional[str] = None
    estado: str
    cantidad_anterior: float
    cantidad_nueva: float
    fecha: datetime

    class Config:
        from_attributes = True


# ── Aprobacion ────────────────────────────────────────────────────────────────

class AprobacionAjusteRequest(BaseModel):
    """Request schema to approve or reject a manual inventory adjustment."""
    estado: EstadoAjusteEnum
    observacion: Optional[str] = None


# ── Alerta ────────────────────────────────────────────────────────────────────

class AlertaResponse(BaseModel):
    """Inventory alert response."""
    id_alerta: int
    id_insumo: int
    estado: str
    semaforo: str
    cantidad_a_pedir: Optional[float] = None
    fecha_creacion: datetime
    fecha_resolucion: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertaListResponse(BaseModel):
    """List of active inventory alerts."""
    total: int
    items: List[AlertaResponse]


# ── Movimiento ────────────────────────────────────────────────────────────────

class MovimientoResponse(BaseModel):
    """Inventory movement response."""
    id_movimiento: int
    id_insumo: int
    tipo: str
    cantidad: float
    motivo: Optional[str] = None
    observacion: Optional[str] = None
    afecta_stock: bool
    cantidad_anterior: float
    cantidad_nueva: float
    estado: str
    fecha: datetime

    class Config:
        from_attributes = True
