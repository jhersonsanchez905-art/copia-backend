"""
pago_schema.py
Pydantic schemas for payment validation (RF-012).

State machine:
  pendiente → aprobado | rechazado  (terminal states)

Author: SebastianValero12
Issue: RF-012 — fix/reservas-transferencias
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EstadoValidacionEnum(str, Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"


# ── Request ───────────────────────────────────────────────────────────────────

class ValidarPagoRequest(BaseModel):
    """Body for PATCH /pagos/{id_pago}/validar.

    Only the target state is required — the validator's identity
    is injected from the authenticated user (current_user).
    """
    estado_validacion: EstadoValidacionEnum = Field(
        ...,
        description="Nuevo estado: 'aprobado' o 'rechazado'. No se permite 'pendiente'.",
    )


# ── Responses ─────────────────────────────────────────────────────────────────

class PagoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pago: int
    id_venta: int
    id_metodo_pago: int
    monto: Decimal
    url_comprobante: Optional[str] = None
    estado_validacion: EstadoValidacionEnum


class PagoDetalleResponse(PagoResponse):
    """Extended response including validation audit fields."""
    fecha_validacion: Optional[datetime] = None
    id_usuario_validacion: Optional[int] = None