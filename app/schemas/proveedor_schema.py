"""
app/schemas/proveedor_schema.py
Pydantic schemas for suppliers and supplier-input relationships.
Author: charlykj
Issue: #38
"""
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class ProveedorBase(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    activo: Optional[bool] = True

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(ProveedorBase):
    nombre: Optional[str] = None

class ProveedorOut(ProveedorBase):
    id_proveedor: int
    class Config:
        from_attributes = True


class InsumoProveedorBase(BaseModel):
    id_insumo: int
    id_proveedor: int
    es_principal: Optional[bool] = False
    precio_referencia: Optional[Decimal] = None
    dias_entrega: Optional[int] = None

class InsumoProveedorCreate(InsumoProveedorBase):
    pass

class InsumoProveedorOut(InsumoProveedorBase):
    id_insumo_proveedor: int
    class Config:
        from_attributes = True