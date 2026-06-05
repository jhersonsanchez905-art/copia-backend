"""
reserva_schema.py
Pydantic schemas for the Reserva API layer.
State machine: pendiente → confirmada | cancelada; confirmada → completada | cancelada
Confirm and cancel require Administrador role.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EstadoReservaEnum(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"
    completada = "completada"


class ReservaBase(BaseModel):
    id_mesa: int
    id_cliente: Optional[int] = None
    fecha_hora: datetime
    num_personas: int = Field(..., ge=1)
    observaciones: Optional[str] = None


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    """Only mutable fields after creation; mesa change requires cancel + re-create."""
    fecha_hora: Optional[datetime] = None
    num_personas: Optional[int] = Field(None, ge=1)
    observaciones: Optional[str] = None


class ReservaResponse(ReservaBase):
    model_config = ConfigDict(from_attributes=True)

    id_reserva: int
    id_usuario: int
    estado: EstadoReservaEnum
    fecha_creacion: datetime
