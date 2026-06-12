"""
producto_schema.py
Esquemas Pydantic para el CRUD de Producto.
Autor: SebastianValero12
Issue: #40
"""

from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


# ── Producto ────────────────────────────────────────────────

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200, examples=["Café Latte"])
    id_categoria: int | None = None
    precio: Decimal = Field(..., gt=0, examples=[8500])
    num_porciones: int | None = Field(None, ge=1)
    url_foto: str | None = None
    pct_prima_real: Decimal | None = None
    activo: bool = True
    fecha_lanzamiento: date | None = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=1, max_length=200)
    id_categoria: int | None = None
    precio: Decimal | None = Field(None, gt=0)
    num_porciones: int | None = Field(None, ge=1)
    url_foto: str | None = None
    pct_prima_real: Decimal | None = None
    activo: bool | None = None
    fecha_lanzamiento: date | None = None


class ProductoResponse(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    fecha_modificacion: datetime | None = None
    costo_produccion: Decimal | None = None