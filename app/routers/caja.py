"""
app/routers/caja.py
HTTP endpoints for cash register module.
Author: Suley Suarez / Jherson
Issue: #16, #40
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_rol
from app.models.catalogo import Usuario
from app.schemas.caja_schema import (
    AperturaCajaRequest,
    AperturaCajaResponse,
    CierreCajaRequest,
    CierreCajaResponse,
)
from app.services import caja_service

router = APIRouter()


@router.post("/apertura", response_model=AperturaCajaResponse, status_code=201)
async def abrir_caja(
    data: AperturaCajaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await caja_service.abrir_caja(data, current_user.id_usuario, db)


@router.get("/apertura/activa", response_model=AperturaCajaResponse)
async def apertura_activa(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await caja_service.get_apertura_activa(db)


@router.post("/cierre", response_model=CierreCajaResponse, status_code=201)
async def cerrar_caja(
    data: CierreCajaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await caja_service.cerrar_caja(data, current_user.id_usuario, db)


@router.get("/cierres", response_model=list[CierreCajaResponse])
async def listar_cierres(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await caja_service.get_cierres(db)


@router.get("/cierres/{id_cierre}", response_model=CierreCajaResponse)
async def obtener_cierre(
    id_cierre: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await caja_service.get_cierre(db, id_cierre)
