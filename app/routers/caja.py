"""
caja.py (router)
Endpoints for cash register: apertura, cierre, and queries.

<<<<<<< HEAD
Author: Suley Suarez / Jherson
=======
Author: Suley Suarez / SebasValero12
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
Issue: #16, #40
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.caja_schema import (
    AperturaCajaRequest,
    AperturaCajaResponse,
    CierreCajaRequest,
    CierreCajaResponse,
)
from app.services import caja_service

router = APIRouter()


# ── Apertura ──────────────────────────────────────────────────────────────────

@router.post("/apertura", response_model=AperturaCajaResponse, status_code=201)
async def abrir_caja(
    data: AperturaCajaRequest,
    db: AsyncSession = Depends(get_db),
):
    """Open a new cash register shift (admin only)."""
    id_usuario = 1  # TODO: extract from Clerk token
    return await caja_service.abrir_caja(data, id_usuario, db)


@router.get("/apertura/activa", response_model=AperturaCajaResponse)
async def apertura_activa(db: AsyncSession = Depends(get_db)):
    """Get the currently active (not yet closed) apertura."""
    return await caja_service.get_apertura_activa(db)


# ── Cierre ────────────────────────────────────────────────────────────────────

@router.post("/cierre", response_model=CierreCajaResponse, status_code=201)
async def cerrar_caja(
    data: CierreCajaRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Close the currently active cash register shift (admin only).
    Calculates expected totals from sales and compares with counted amounts.
    """
    id_usuario = 1  # TODO: extract from Clerk token
    return await caja_service.cerrar_caja(data, id_usuario, db)


@router.get("/cierres", response_model=list[CierreCajaResponse])
async def listar_cierres(db: AsyncSession = Depends(get_db)):
    """List all cash register closings (admin only)."""
    return await caja_service.get_cierres(db)


@router.get("/cierres/{id_cierre}", response_model=CierreCajaResponse)
async def obtener_cierre(
    id_cierre: int, db: AsyncSession = Depends(get_db)
):
    """Get a specific cash register closing with details."""
    return await caja_service.get_cierre(db, id_cierre)
