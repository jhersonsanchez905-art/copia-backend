"""
venta_schema.py
Pydantic schemas for sales module request and response validation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


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
    cantidad: int = Field(default=1, ge=1, description="Cantidad vendida — debe ser mayor a 0")


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


# ── MetodoPago ────────────────────────────────────────────────────────────────

class MetodoPagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_metodo_pago: int
    nombre: str
    requiere_comprobante: bool


# ── Pago ──────────────────────────────────────────────────────────────────────

class PagoRequest(BaseModel):
    id_metodo_pago: int
    monto: Decimal = Field(gt=0, description="Monto del pago — debe ser mayor a 0")
    url_comprobante: Optional[str] = None


class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pago: int
    id_venta: int
    id_metodo_pago: int
    monto: Decimal
    url_comprobante: Optional[str] = None
    estado_validacion: EstadoValidacionEnum
    metodo_pago: MetodoPagoResponse


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


# ── Venta ─────────────────────────────────────────────────────────────────────

class VentaCreateRequest(BaseModel):
    """
    Request body for `POST /api/v1/ventas/`.

    ## Idempotency

    Supply `token_idempotencia` to make retries safe. The frontend should
    generate a UUID when the cashier initiates payment and reuse that same
    token for any subsequent retry (double-click, timeout, browser refresh).

    ```json
    {
      "token_idempotencia": "sale-8c7e3f4a-2026-06-12",
      "turno": "manana",
      "id_apertura": 1,
      "productos": [{"id_producto": 3, "cantidad": 2}],
      "pagos": [{"id_metodo_pago": 1, "monto": "10000"}]
    }
    ```

    If a sale with this token was already completed the API returns that
    existing sale — no new inventory movements, payments, or invoice are
    created. The frontend does not need any special retry logic.
    """

    turno: TurnoEnum
    id_apertura: int
    id_pedido: Optional[int] = None
    id_cliente: Optional[int] = None
    productos: list[ItemVentaRequest]
    pagos: list[PagoRequest]
    token_idempotencia: Optional[str] = Field(default=None, max_length=64)

    @field_validator("token_idempotencia", mode="before")
    @classmethod
    def normalizar_token(cls, v: object) -> str | None:
        if v is None:
            return None
        stripped = str(v).strip()
        return stripped or None

    @model_validator(mode="after")
    def validar_request(self) -> "VentaCreateRequest":
        if not self.productos:
            raise ValueError("La venta debe incluir al menos un producto")
        if not self.pagos:
            raise ValueError("La venta debe incluir al menos un pago")
        ids_producto = [p.id_producto for p in self.productos]
        if len(ids_producto) != len(set(ids_producto)):
            raise ValueError("No se permiten productos duplicados en la misma venta")
        return self


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

    @computed_field  # type: ignore[misc]
    @property
    def cambio(self) -> Decimal:
        """Amount returned to the customer when total paid exceeds the sale subtotal."""
        diff = self.total - self.subtotal
        return diff if diff > Decimal("0") else Decimal("0")
