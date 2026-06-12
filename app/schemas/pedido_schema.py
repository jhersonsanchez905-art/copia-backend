"""
pedido_schema.py
Pydantic schemas for Pedido, PedidoItem, and PedidoServicio.
Mesero flow: abierto → enviado → pagado | cancelado
PedidoItem flow: pendiente → en_preparacion → listo → entregado | cancelado
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EstadoPedidoEnum(str, Enum):
    abierto = "abierto"
    enviado = "enviado"
    pagado = "pagado"
    cancelado = "cancelado"


class EstadoPedidoItemEnum(str, Enum):
    pendiente = "pendiente"
    en_preparacion = "en_preparacion"
    listo = "listo"
    entregado = "entregado"
    cancelado = "cancelado"


# ── PedidoItem ────────────────────────────────────────────────────────────────

class PedidoItemBase(BaseModel):
    id_producto: int
    cantidad: int = Field(..., ge=1)
    precio_unitario: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None


class PedidoItemCreate(PedidoItemBase):
    pass


class PedidoItemUpdate(BaseModel):
    cantidad: Optional[int] = Field(None, ge=1)
    precio_unitario: Optional[Decimal] = Field(None, gt=0)
    observaciones: Optional[str] = None
    estado: Optional[EstadoPedidoItemEnum] = None


class PedidoItemResponse(PedidoItemBase):
    model_config = ConfigDict(from_attributes=True)

    id_pedido_item: int
    id_pedido: int
    subtotal: Decimal
    estado: EstadoPedidoItemEnum


# ── PedidoServicio ────────────────────────────────────────────────────────────

class PedidoServicioBase(BaseModel):
    id_servicio: int
    cantidad: int = Field(1, ge=1)
    valor_unitario: Decimal = Field(..., gt=0)
    observaciones: Optional[str] = None


class PedidoServicioCreate(PedidoServicioBase):
    pass


class PedidoServicioResponse(PedidoServicioBase):
    model_config = ConfigDict(from_attributes=True)

    id_pedido_servicio: int
    id_pedido: int
    subtotal: Decimal


# ── Pedido ────────────────────────────────────────────────────────────────────

class PedidoBase(BaseModel):
    id_mesa: int
    id_reserva: Optional[int] = None
    observaciones: Optional[str] = None


class PedidoCreate(PedidoBase):
    items: list[PedidoItemCreate] = Field(default_factory=list)
    servicios: list[PedidoServicioCreate] = Field(default_factory=list)


class PedidoUpdate(BaseModel):
    observaciones: Optional[str] = None


class PedidoResponse(PedidoBase):
    model_config = ConfigDict(from_attributes=True)

    id_pedido: int
    id_usuario: int
    fecha_hora: datetime
    estado: EstadoPedidoEnum
    total: Decimal = Decimal("0")
    items: list[PedidoItemResponse] = []
    servicios: list[PedidoServicioResponse] = []
