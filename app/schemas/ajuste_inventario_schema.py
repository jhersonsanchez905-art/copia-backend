"""
ajuste_inventario_schema.py
Schemas Pydantic para ajustes manuales de inventario con flujo de aprobación.
Autor: Ivan Ospino
Issue: #21
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EstadoAjusteEnum(str, Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


class AjusteInventarioCreate(BaseModel):
    id_insumo: int
    cantidad: Decimal = Field(..., description="Positivo para ingresar stock, negativo para descontar")
    motivo: str = Field(..., min_length=1)
    observacion: Optional[str] = None


class AjusteInventarioAprobar(BaseModel):
    observacion: Optional[str] = None


class AjusteInventarioRechazar(BaseModel):
    observacion: Optional[str] = None


class AjusteInventarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ajuste: int
    id_insumo: int
    id_usuario_solicita: int
    id_usuario_aprueba: Optional[int] = None
    cantidad: Decimal
    motivo: str
    observacion: Optional[str] = None
    estado: EstadoAjusteEnum
    fecha_solicitud: datetime
    fecha_resolucion: Optional[datetime] = None