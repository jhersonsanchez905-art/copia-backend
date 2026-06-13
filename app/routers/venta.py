"""
app/routers/venta.py
HTTP endpoints for sales module.
Author: Suley Suarez
Issue: #16
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.limiter import limiter
from app.database import get_db
from app.dependencies import get_current_user, require_rol
from app.models.catalogo import Usuario
from app.schemas.venta_schema import VentaCreateRequest, VentaResponse
from app.services import venta_service

router = APIRouter()


@router.post("/", response_model=VentaResponse, status_code=201)
@limiter.limit("30/minute")
async def registrar_venta(
    request: Request,
    data: VentaCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("cajero", "administrador")),
):
    return await venta_service.registrar_venta(data, current_user.id_usuario, db)


@router.get("/{id_venta}", response_model=VentaResponse)
async def get_venta(id_venta: int, db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return await venta_service.get_venta_by_id(id_venta, db)


@router.get("/", response_model=list[VentaResponse])
async def get_ventas(
    fecha: date = Query(..., description="Date to filter sales (YYYY-MM-DD)"),
    turno: Optional[str] = Query(None, description="Shift: manana or tarde"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await venta_service.get_ventas_by_fecha_turno(fecha, turno, db)
