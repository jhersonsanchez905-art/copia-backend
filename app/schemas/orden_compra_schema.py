"""
orden_compra_schema.py
Schemas Pydantic para órdenes de compra y sus líneas de detalle.
Autor: Ivan Ospino
Issue: #21
"""
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class EstadoOrdenCompraEnum(str, Enum):
    borrador = "borrador"
    enviada = "enviada"
    recibida = "recibida"
    cancelada = "cancelada"


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

class OrdenCompraDetalleCreate(BaseModel):
    id_insumo: int
    cantidad_solicitada: Decimal
    precio_unitario: Optional[Decimal] = Decimal("0")
    notas: Optional[str] = None


class OrdenCompraDetalleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_detalle: int
    id_orden_compra: int
    id_insumo: int
    cantidad_solicitada: Decimal
    cantidad_recibida: Decimal
    precio_unitario: Decimal
    subtotal_linea: Decimal
    notas: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime


# ── Recepción ─────────────────────────────────────────────────────────────────

class OrdenCompraRecibirDetalle(BaseModel):
    id_insumo: int
    cantidad_recibida: Decimal


class OrdenCompraRecibir(BaseModel):
    detalles: List[OrdenCompraRecibirDetalle]


# ── OrdenCompra ───────────────────────────────────────────────────────────────

class OrdenCompraCreate(BaseModel):
    id_proveedor: Optional[int] = None
    id_usuario: Optional[int] = None
    numero_orden: str
    fecha_emision: Optional[date] = None
    fecha_entrega_esperada: Optional[date] = None
    notas: Optional[str] = None
    detalles: Optional[List[OrdenCompraDetalleCreate]] = []


class OrdenCompraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_orden_compra: int
    id_proveedor: Optional[int] = None
    id_usuario: Optional[int] = None
    numero_orden: str
    fecha_emision: Optional[date] = None
    fecha_entrega_esperada: Optional[date] = None
    fecha_recepcion_real: Optional[date] = None
    estado: EstadoOrdenCompraEnum
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    notas: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    detalles: List[OrdenCompraDetalleOut] = []