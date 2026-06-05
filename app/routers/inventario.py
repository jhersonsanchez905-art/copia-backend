"""
app/routers/inventario.py

HTTP endpoints for inventory module.
Delegates all business logic to inventario_service.

Endpoints:
    POST   /api/v1/inventario/ajustes                        register manual adjustment
    PATCH  /api/v1/inventario/ajustes/{id_movimiento}/aprobar  approve or reject adjustment
    GET    /api/v1/inventario/alertas                        get all active alerts

Author: Suley Suarez
Issue: #16
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import inventario_service
from app.schemas.inventario_schema import (
    AjusteInventarioRequest,
    AjusteInventarioResponse,
    AprobacionAjusteRequest,
    AlertaResponse
)

router = APIRouter()


@router.post("/ajustes", response_model=AjusteInventarioResponse, status_code=201)
async def registrar_ajuste(
    data: AjusteInventarioRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a manual inventory adjustment with status PENDIENTE.
    Does NOT modify stock until approved by an admin.
    Sends email notification to admin automatically.
    """
    # TODO: get id_usuario from Clerk token
    id_usuario = 1  # placeholder
    return await inventario_service.registrar_ajuste_manual(data, id_usuario, db)


@router.patch("/ajustes/{id_movimiento}/aprobar", response_model=AjusteInventarioResponse)
async def aprobar_ajuste(
    id_movimiento: int,
    data: AprobacionAjusteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a pending manual inventory adjustment.
    If approved, updates stock and checks alert thresholds.
    Only admin role can call this endpoint — returns HTTP 403 otherwise.
    """
    # TODO: get id_usuario from Clerk token and validate admin role
    id_aprobador = 1  # placeholder
    return await inventario_service.aprobar_ajuste(id_movimiento, data, id_aprobador, db)


@router.get("/alertas", response_model=list[AlertaResponse])
async def get_alertas(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active inventory alerts.
    Used by the dashboard traffic light system.
    """
    return await inventario_service.get_alertas_activas(db)
