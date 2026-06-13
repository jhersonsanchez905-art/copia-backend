"""
app/routers/venta.py
HTTP endpoints for sales module.
Author: Suley Suarez
Issue: #16
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_rol
from app.limiter import limiter
from app.models.catalogo import Usuario
from app.schemas.venta_schema import VentaCreateRequest, VentaResponse
from app.services import venta_service

router = APIRouter()


@router.post(
    "/",
    response_model=VentaResponse,
    status_code=201,
    summary="Registrar venta",
    description=(
        "Registra una venta nueva de forma atómica: descuenta stock, crea pagos y emite factura.\n\n"
        "**Idempotencia**: Incluye `token_idempotencia` para que los reintentos sean seguros. "
        "El frontend debe generar un UUID cuando el cajero inicia el cobro y reusar ese mismo "
        "token en cualquier reintento (doble clic, timeout, recarga de página).\n\n"
        "Si ya existe una venta con ese token el endpoint devuelve esa venta existente — "
        "no se crea ningún movimiento de inventario, pago ni factura adicionales.\n\n"
        "Ejemplo de body con token:\n"
        "```json\n"
        '{"token_idempotencia": "sale-8c7e3f4a-2026-06-12", "turno": "manana", '
        '"id_apertura": 1, "productos": [{"id_producto": 3, "cantidad": 2}], '
        '"pagos": [{"id_metodo_pago": 1, "monto": "10000"}]}\n'
        "```"
    ),
)
@limiter.limit("30/minute")
async def registrar_venta(
    request: Request,
    data: VentaCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("cajero", "administrador")),
):
    es_admin = current_user.rol.nombre == "administrador"
    return await venta_service.registrar_venta(data, current_user.id_usuario, db, es_admin=es_admin)


@router.get("/{id_venta}", response_model=VentaResponse)
async def get_venta(id_venta: int, db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return await venta_service.get_venta_by_id(id_venta, db)


@router.get("/", response_model=list[VentaResponse])
async def get_ventas(
    fecha: Optional[date] = Query(default=None, description="Date to filter sales (YYYY-MM-DD). Defaults to today."),
    turno: Optional[str] = Query(None, description="Shift: manana or tarde"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await venta_service.get_ventas_by_fecha_turno(fecha, turno, db)
