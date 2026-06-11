"""
app/schemas/caja_schema.py

Pydantic schemas for cash register module request and response validation.

Author: Suley Suarez
Issue: #16
"""
from decimal import Decimal
from enum import Enum
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator


class TurnoEnum(str, Enum):
    manana = "manana"
    tarde  = "tarde"


# ── Denominaciones ────────────────────────────────────────────────────────────

class DenominacionResponse(BaseModel):
    """A single denomination from the master catalogue."""
    id_denominacion: int
    valor:           Decimal
    tipo:            str
    activo:          bool

    class Config:
        from_attributes = True


class ArqueoDenominacionRequest(BaseModel):
    """One denomination line in an opening or closing arqueo."""
    id_denominacion: int
    cantidad:        int

    @field_validator("cantidad")
    @classmethod
    def cantidad_no_negativa(cls, v: int) -> int:
        if v < 0:
            raise ValueError("La cantidad de denominaciones no puede ser negativa")
        return v


class ArqueoDenominacionResponse(BaseModel):
    """Denomination line returned in apertura/cierre responses."""
    id_denominacion: int
    valor:           Decimal
    tipo:            str
    cantidad:        int
    subtotal:        Decimal

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def flatten_denominacion(cls, obj):
        """Flatten the nested Denominacion ORM relationship into scalar fields."""
        if hasattr(obj, "denominacion") and obj.denominacion is not None:
            return {
                "id_denominacion": obj.id_denominacion,
                "valor":           obj.denominacion.valor,
                "tipo":            obj.denominacion.tipo,
                "cantidad":        obj.cantidad,
                "subtotal":        obj.subtotal,
            }
        return obj


# ── Apertura Caja ─────────────────────────────────────────────────────────────

class AperturaCajaRequest(BaseModel):
    """Request schema to open a cash register shift."""
    turno:         TurnoEnum
    fecha:         date
    monto_inicial: Decimal
    observaciones: Optional[str] = None
    arqueo:        List[ArqueoDenominacionRequest] = []

    @field_validator("monto_inicial")
    @classmethod
    def monto_inicial_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El monto inicial no puede ser negativo")
        return v

    @model_validator(mode="after")
    def validar_arqueo(self) -> "AperturaCajaRequest":
        ids = [d.id_denominacion for d in self.arqueo]
        if len(ids) != len(set(ids)):
            raise ValueError("Denominaciones duplicadas en el arqueo de apertura")
        return self


class AperturaCajaResponse(BaseModel):
    """Cash register opening response."""
    id_apertura:   int
    id_usuario:    int
    turno:         str
    fecha:         date
    monto_inicial: Decimal
    hora_apertura: datetime
    observaciones: Optional[str] = None
    arqueo:        List[ArqueoDenominacionResponse] = []

    class Config:
        from_attributes = True


# ── Cierre Caja ───────────────────────────────────────────────────────────────

class CierreCajaDetalleRequest(BaseModel):
    """Payment method breakdown for cash register closing."""
    id_metodo_pago: int
    total_contado:  Decimal

    @field_validator("total_contado")
    @classmethod
    def total_contado_no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El monto contado no puede ser negativo")
        return v


class CierreCajaRequest(BaseModel):
    """Request schema to close a cash register shift."""
    observaciones:   Optional[str] = None
    detalle:         List[CierreCajaDetalleRequest]
    arqueo_efectivo: List[ArqueoDenominacionRequest] = []

    @model_validator(mode="after")
    def validar_cierre(self) -> "CierreCajaRequest":
        if not self.detalle:
            raise ValueError("Debe incluir al menos un detalle de cierre")
        ids_metodo = [d.id_metodo_pago for d in self.detalle]
        if len(ids_metodo) != len(set(ids_metodo)):
            raise ValueError("No se permiten métodos de pago duplicados en el mismo cierre")
        ids_den = [d.id_denominacion for d in self.arqueo_efectivo]
        if len(ids_den) != len(set(ids_den)):
            raise ValueError("Denominaciones duplicadas en el arqueo de cierre")
        return self


class CierreCajaDetalleResponse(BaseModel):
    """Payment method detail in cash register closing response."""
    id_metodo_pago: int
    total_esperado: Decimal
    total_contado:  Decimal
    diferencia:     Decimal

    class Config:
        from_attributes = True


class CierreCajaResponse(BaseModel):
    """Cash register closing response."""
    id_cierre:           int
    id_apertura:         int
    id_usuario:          int
    turno:               str
    fecha:               date
    total_general:       Decimal
    total_transacciones: Decimal
    diferencia:          Decimal
    hora_cierre:         datetime
    observaciones:       Optional[str] = None
    detalle:             List[CierreCajaDetalleResponse] = []
    arqueo_efectivo:     List[ArqueoDenominacionResponse] = []

    class Config:
        from_attributes = True
