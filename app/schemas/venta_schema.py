"""
app/schemas/venta_schema.py

Pydantic schemas for sales module request and response validation.

Author: Suley Suarez
Issue: #16
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TurnoEnum(str, Enum):
    manana = "manana"
    tarde = "tarde"


class EstadoVentaEnum(str, Enum):
    abierta = "abierta"
    cerrada = "cerrada"
    anulada = "anulada"


# ── Item Venta ────────────────────────────────────────────────────────────────

class ItemVentaRequest(BaseModel):
    """Single product item in a sale request."""
    id_producto: int
    cantidad: int


# ── Pago ─────────────────────────────────────────────────────────────────────

class PagoRequest(BaseModel):
    """Payment method detail in a sale request."""
    id_metodo_pago: int
    monto: float
    url_comprobante: Optional[str] = None


class PagoResponse(BaseModel):
    """Payment method detail in a sale response."""
    id_pago: int
    id_metodo_pago: int
    monto: float
    url_comprobante: Optional[str] = None
    estado_validacion: Optional[str] = None

    class Config:
        from_attributes = True


# ── Venta ─────────────────────────────────────────────────────────────────────

class VentaCreateRequest(BaseModel):
    """
    Request schema to register a new sale.
    A single sale can have multiple products and multiple payment methods.
    """
    turno: TurnoEnum
    id_apertura: int
    id_cliente: Optional[int] = None
    productos: List[ItemVentaRequest]
    pagos: List[PagoRequest]


class ItemVentaResponse(BaseModel):
    """Single product item in a sale response."""
    id_item_venta: int
    id_producto: int
    id_receta_version: Optional[int] = None
    cantidad: int
    precio_unitario: float
    subtotal: float
    receta_snapshot: Optional[dict] = None

    class Config:
        from_attributes = True


class FacturaResponse(BaseModel):
    """Invoice associated to a sale."""
    id_factura: int
    numero: str
    fecha_emision: datetime
    total: float
    url_pdf: Optional[str] = None

    class Config:
        from_attributes = True


class VentaResponse(BaseModel):
    """Full sale response including items, payments and invoice."""
    id_venta: int
    turno: str
    fecha: datetime
    id_usuario: int
    id_cliente: Optional[int] = None
    subtotal: float
    total: float
    estado: str
    items: List[ItemVentaResponse] = []
    pagos: List[PagoResponse] = []
    factura: Optional[FacturaResponse] = None

    class Config:
        from_attributes = True


class VentaListResponse(BaseModel):
    """Paginated list of sales."""
    total: int
    items: List[VentaResponse]


# ── Devolucion ────────────────────────────────────────────────────────────────

class DevolucionCreateRequest(BaseModel):
    """Request schema to register a return."""
    id_item_venta: int
    motivo: str
    observacion: Optional[str] = None
    reintegra_stock: bool = False


class DevolucionResponse(BaseModel):
    """Return response."""
    id_devolucion: int
    id_venta: int
    id_item_venta: int
    fecha: datetime
    motivo: str
    estado: str
    reintegra_stock: bool

    class Config:
        from_attributes = True
