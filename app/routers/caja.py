"""
app/routers/caja.py

HTTP endpoints for cash register module.
Delegates all business logic to caja_service.

Endpoints:
    POST   /api/v1/caja/apertura              open a new shift
    POST   /api/v1/caja/{id_apertura}/cierre  close a shift

Author: Suley Suarez
Issue: #16
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import caja_service
from app.schemas.caja_schema import (
    AperturaCajaRequest,
    AperturaCajaResponse,
    CierreCajaRequest,
    CierreCajaResponse
)

router = APIRouter()


@router.post("/apertura", response_model=AperturaCajaResponse, status_code=201)
async def abrir_caja(
    data: AperturaCajaRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Open a new cash register shift.
    Records the initial cash amount for the shift.
    Only one opening per user per shift is allowed.
    """
    # TODO: get id_usuario from Clerk token
    id_usuario = 1  # placeholder
    return await caja_service.abrir_caja(data, id_usuario, db)


@router.post("/{id_apertura}/cierre", response_model=CierreCajaResponse, status_code=201)
async def cerrar_caja(
    id_apertura: int,
    data: CierreCajaRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Close a cash register shift.
    Calculates expected totals from sales and compares with counted amounts.
    Only admin role can close the register.
    """
    # TODO: get id_usuario from Clerk token and validate admin role
    id_usuario = 1  # placeholder
    return await caja_service.cerrar_caja(id_apertura, data, id_usuario, db)
