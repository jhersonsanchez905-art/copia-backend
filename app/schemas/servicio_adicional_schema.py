"""
servicio_adicional_schema.py
Pydantic schemas for ServicioAdicional.
"""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ServicioAdicionalBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: Optional[str] = None
    valor: Decimal = Field(..., gt=0)
    activo: bool = True


class ServicioAdicionalCreate(ServicioAdicionalBase):
    pass


class ServicioAdicionalUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=120)
    descripcion: Optional[str] = None
    valor: Optional[Decimal] = Field(None, gt=0)
    activo: Optional[bool] = None


class ServicioAdicionalResponse(ServicioAdicionalBase):
    model_config = ConfigDict(from_attributes=True)

    id_servicio: int
