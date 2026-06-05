"""
inventario_schema.py
Pydantic schemas for MovimientoInventario, Alerta, and read-only Auditoria queries.
AjusteInventario has its own schema file (ajuste_inventario_schema.py).
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TipoMovimientoEnum(str, Enum):
    entrada = "entrada"
    salida = "salida"
    merma = "merma"


class SemaforoEnum(str, Enum):
    verde = "verde"
    amarillo = "amarillo"
    rojo = "rojo"


class TipoAlertaEnum(str, Enum):
    stock_bajo = "stock_bajo"
    stock_critico = "stock_critico"


class EstadoAlertaEnum(str, Enum):
    activa = "activa"
    resuelta = "resuelta"


# ── MovimientoInventario ──────────────────────────────────────────────────────

class MovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_movimiento: int
    id_insumo: int
    tipo: TipoMovimientoEnum
    cantidad: Decimal
    cantidad_anterior: Decimal
    cantidad_nueva: Decimal
    motivo: Optional[str] = None
    observacion: Optional[str] = None
    id_venta: Optional[int] = None
    id_orden_compra: Optional[int] = None
    id_usuario: int
    fecha: datetime


# ── Alerta ────────────────────────────────────────────────────────────────────

class AlertaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_alerta: int
    id_insumo: int
    tipo: TipoAlertaEnum
    estado: EstadoAlertaEnum
    semaforo: SemaforoEnum
    cantidad_a_pedir: Optional[Decimal] = None
    id_orden_compra: Optional[int] = None
    fecha_creacion: datetime
    fecha_resolucion: Optional[datetime] = None
