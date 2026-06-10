"""
devolucion_schema.py
Pydantic schemas for Devolucion (returns) module.
States: pendiente → aprobada | rechazada

<<<<<<< HEAD
Author: Jherson
=======
Author: SebasValero12
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
Issue: #40
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EstadoDevolucionEnum(str, Enum):
    pendiente = "pendiente"
    aprobada = "aprobada"
    rechazada = "rechazada"


class DevolucionCreate(BaseModel):
    id_venta: int
    id_item_venta: int
    cantidad: int = Field(..., ge=1)
    motivo: str
    observacion: Optional[str] = None
    reintegra_stock: bool = True


class DevolucionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_devolucion: int
    id_venta: int
    id_item_venta: int
    id_aprobador: Optional[int] = None
    cantidad: int
    motivo: str
    observacion: Optional[str] = None
    estado: EstadoDevolucionEnum
    reintegra_stock: int
    fecha: datetime
