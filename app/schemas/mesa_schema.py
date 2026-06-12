"""
mesa_schema.py
Pydantic schemas for Mesa.
State machine: disponible → ocupada | reservada → disponible

Reserva schemas have been moved to reserva_schema.py (single source of truth).

Author: Suley Suarez / SebastianValero12
Issue: fix/reservas-transferencias
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EstadoMesaEnum(str, Enum):
    disponible = "disponible"
    ocupada = "ocupada"
    reservada = "reservada"


# ── Mesa ──────────────────────────────────────────────────────────────────────

class MesaBase(BaseModel):
    numero: str = Field(..., min_length=1, max_length=10)
    capacidad: int = Field(..., ge=1)
    zona: Optional[str] = Field(None, max_length=60)
    activo: bool = True


class MesaCreate(MesaBase):
    pass


class MesaUpdate(BaseModel):
    numero: Optional[str] = Field(None, min_length=1, max_length=10)
    capacidad: Optional[int] = Field(None, ge=1)
    zona: Optional[str] = None
    activo: Optional[bool] = None


class MesaResponse(MesaBase):
    model_config = ConfigDict(from_attributes=True)

    id_mesa: int
    estado: EstadoMesaEnum