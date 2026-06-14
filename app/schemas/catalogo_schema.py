"""
app/schemas/catalogo_schema.py
Pydantic schemas for the base catalog models of the POS system.
Author: charlykj
Issue: #38
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RolCreate(RolBase):
    pass

class RolOut(RolBase):
    id_rol: int
    class Config:
        from_attributes = True


class UsuarioBase(BaseModel):
    clerk_id: str
    nombre: str
    correo: str
    id_rol: Optional[int] = None
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    id_rol: Optional[int] = None
    activo: Optional[bool] = None

class UsuarioOut(UsuarioBase):
    id_usuario: int
    fecha_creacion: Optional[datetime] = None
    rol: Optional[RolOut] = None
    class Config:
        from_attributes = True


class ClienteBase(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    numero_documento: Optional[str] = None
    activo: Optional[bool] = True
    observaciones: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    nombre: Optional[str] = None

class ClienteOut(ClienteBase):
    id_cliente: int
    fecha_registro: Optional[datetime] = None
    class Config:
        from_attributes = True


class MarcaBase(BaseModel):
    nombre: str

class MarcaCreate(MarcaBase):
    pass

class MarcaOut(MarcaBase):
    id_marca: int
    class Config:
        from_attributes = True


class UnidadMedidaBase(BaseModel):
    nombre: str
    abreviatura: str

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedidaOut(UnidadMedidaBase):
    id_unidad: int
    class Config:
        from_attributes = True


class ClasificacionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ClasificacionCreate(ClasificacionBase):
    pass

class ClasificacionOut(ClasificacionBase):
    id_clasificacion: int
    class Config:
        from_attributes = True


class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaOut(CategoriaBase):
    id_categoria: int
    class Config:
        from_attributes = True


class MetodoPagoBase(BaseModel):
    nombre: str
    requiere_comprobante: Optional[bool] = False
    activo: Optional[bool] = True

class MetodoPagoCreate(MetodoPagoBase):
    pass

class MetodoPagoOut(MetodoPagoBase):
    id_metodo_pago: int
    class Config:
        from_attributes = True