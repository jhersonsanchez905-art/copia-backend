"""
orden_compra_schema.py
Schemas Pydantic para validación y serialización de órdenes de compra y sus líneas de detalle.
Autor: Ivan Ospino
Issue: #20
"""

from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from app.models.orden_compra import EstadoOrdenCompra


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

class OrdenCompraDetalleBase(BaseModel):
    id_insumo: int
    cantidad_solicitada: Decimal
    precio_unitario: Optional[Decimal] = Decimal("0")
    notas: Optional[str] = None


class OrdenCompraDetalleCreate(OrdenCompraDetalleBase):
    pass


class OrdenCompraDetalleUpdate(BaseModel):
    cantidad_solicitada: Optional[Decimal] = None
    cantidad_recibida: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    notas: Optional[str] = None


class OrdenCompraDetalleOut(OrdenCompraDetalleBase):
    id_detalle: int
    id_orden_compra: int
    cantidad_recibida: Decimal
    subtotal_linea: Decimal
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


# ── OrdenCompra ───────────────────────────────────────────────────────────────

class OrdenCompraBase(BaseModel):
    id_proveedor: Optional[int] = None
    id_usuario: Optional[int] = None
    numero_orden: str
    fecha_emision: Optional[date] = None
    fecha_entrega_esperada: Optional[date] = None
    notas: Optional[str] = None


class OrdenCompraCreate(OrdenCompraBase):
    detalles: Optional[List[OrdenCompraDetalleCreate]] = []


class OrdenCompraUpdate(BaseModel):
    id_proveedor: Optional[int] = None
    fecha_entrega_esperada: Optional[date] = None
    fecha_recepcion_real: Optional[date] = None
    estado: Optional[EstadoOrdenCompra] = None
    notas: Optional[str] = None


class OrdenCompraOut(OrdenCompraBase):
    id_orden_compra: int
    fecha_recepcion_real: Optional[date] = None
    estado: EstadoOrdenCompra
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    detalles: List[OrdenCompraDetalleOut] = []

    class Config:
        from_attributes = True