"""
venta_schema.py
Pydantic schemas for sales module request and response validation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class TurnoEnum(str, Enum):
    manana = "manana"
    tarde = "tarde"


class EstadoVentaEnum(str, Enum):
    abierta = "abierta"
    completada = "completada"
    anulada = "anulada"


class EstadoValidacionEnum(str, Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


# ── ItemVenta ─────────────────────────────────────────────────────────────────

class ItemVentaRequest(BaseModel):
    id_producto: int
    cantidad: int = 1


class ItemVentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item_venta: int
    id_venta: int
    id_producto: int
    id_receta_version: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    receta_snapshot: Optional[Any] = None


# ── Pago ──────────────────────────────────────────────────────────────────────

class PagoRequest(BaseModel):
    id_metodo_pago: int
    monto: Decimal
    url_comprobante: Optional[str] = None


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pago: int
    id_venta: int
    id_metodo_pago: int
    monto: Decimal
    url_comprobante: Optional[str] = None
    estado_validacion: EstadoValidacionEnum


class ValidarPagoRequest(BaseModel):
    estado_validacion: EstadoValidacionEnum
    id_usuario_validacion: int


class PagoDetalleResponse(PagoResponse):
    """Respuesta extendida con campos de validación."""
    fecha_validacion: Optional[datetime] = None
    id_usuario_validacion: Optional[int] = None


# ── Factura ───────────────────────────────────────────────────────────────────

class FacturaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_factura: int
    numero: str
    fecha_emision: datetime
    total: Decimal
    url_pdf: Optional[str] = None


# ── Devolucion ────────────────────────────────────────────────────────────────

class DevolucionCreateRequest(BaseModel):
    id_item_venta: int
    motivo: str
    observacion: Optional[str] = None
    reintegra_stock: bool = False


class DevolucionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_devolucion: int
    id_venta: int
    id_item_venta: int
    fecha: datetime
    motivo: str
    estado: str
    reintegra_stock: int


# ── Venta ──────────────────────────────────────────────────────────────────────

class VentaCreateRequest(BaseModel):
    turno: TurnoEnum
    id_apertura: int
    id_pedido: Optional[int] = None
    id_cliente: Optional[int] = None
    productos: list[ItemVentaRequest]
    pagos: list[PagoRequest]


class VentaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_venta: int
    id_apertura: int
    id_pedido: Optional[int] = None
    id_usuario: int
    id_cliente: Optional[int] = None
    turno: str
    fecha: datetime
    subtotal: Decimal
    total: Decimal
    estado: EstadoVentaEnum
    items: list[ItemVentaResponse] = []
    pagos: list[PagoResponse] = []
    factura: Optional[FacturaResponse] = None
