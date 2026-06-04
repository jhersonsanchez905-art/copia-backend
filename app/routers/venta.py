"""
app/routers/venta.py

HTTP endpoints for sales module.
Delegates all business logic to venta_service.

Endpoints:
    POST   /api/v1/ventas                  register a new sale
    GET    /api/v1/ventas/{id_venta}       get sale by ID
    GET    /api/v1/ventas                  get sales by date and shift

Author: Suley Suarez
Issue: #16
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional
from app.database import get_db
from app.services import venta_service
from app.schemas.venta_schema import (
    VentaCreateRequest,
    VentaResponse,
    VentaListResponse
)

router = APIRouter()


@router.post("/", response_model=VentaResponse, status_code=201)
async def registrar_venta(
    data: VentaCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new sale.

    - Verifies stock for all ingredients before deducting.
    - If any ingredient is insufficient returns HTTP 400.
    - All operations run in a single atomic transaction.
    - Automatically generates the invoice on closing.
    """
    # TODO: get id_usuario from Clerk token
    id_usuario = 1  # placeholder
    return await venta_service.registrar_venta(data, id_usuario, db)


@router.get("/{id_venta}", response_model=VentaResponse)
async def get_venta(
    id_venta: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a sale by its ID including items, payments and invoice.

    Raises HTTP 404 if the sale does not exist.
    """
    return await venta_service.get_venta_by_id(id_venta, db)


@router.get("/", response_model=list[VentaResponse])
async def get_ventas(
    fecha: date = Query(..., description="Date to filter sales (YYYY-MM-DD)"),
    turno: Optional[str] = Query(None, description="Shift: manana or tarde"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all sales for a given date and optional shift.
    Used by the cash register closing and daily reports.
    """
    return await venta_service.get_ventas_by_fecha_turno(fecha, turno, db)
