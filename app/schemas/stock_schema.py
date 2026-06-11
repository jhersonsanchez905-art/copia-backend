"""
stock_schema.py
Pydantic schemas for Stock (read-only semaforo status).
Stock is managed automatically — never updated directly via API.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SemaforoEnum(str, Enum):
    verde = "verde"
    amarillo = "amarillo"
    rojo = "rojo"


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_stock: int
    id_insumo: int
    cantidad: Decimal
    semaforo: SemaforoEnum
    ultima_actualizacion: Optional[datetime] = None
