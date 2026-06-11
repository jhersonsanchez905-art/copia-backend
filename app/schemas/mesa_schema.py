"""
mesa_schema.py
Pydantic schemas for Mesa and Reserva.
State machines:
  Mesa: disponible → ocupada | reservada → disponible
  Reserva: pendiente → confirmada | cancelada; confirmada → completada | cancelada
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EstadoMesaEnum(str, Enum):
    disponible = "disponible"
    ocupada = "ocupada"
    reservada = "reservada"


class EstadoReservaEnum(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"
    completada = "completada"


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


# ── Reserva ───────────────────────────────────────────────────────────────────

class ReservaBase(BaseModel):
    id_mesa: int
    id_cliente: Optional[int] = None
    fecha_hora: datetime
    num_personas: int = Field(..., ge=1)
    observaciones: Optional[str] = None


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    id_mesa: Optional[int] = None
    id_cliente: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    num_personas: Optional[int] = Field(None, ge=1)
    observaciones: Optional[str] = None


class ReservaResponse(ReservaBase):
    model_config = ConfigDict(from_attributes=True)

    id_reserva: int
    id_usuario: int
    estado: EstadoReservaEnum
    fecha_creacion: datetime
