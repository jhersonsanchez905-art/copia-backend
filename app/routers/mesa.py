"""
mesa.py (router)
Endpoints for Mesa management with state machine enforcement.

Reserva mutation endpoints have been removed — use /api/v1/reservas instead.
Only GET /mesas/{id_mesa}/reservas is kept as a convenience query.

Author: Suley Suarez / SebastianValero12
Issue: fix/reservas-transferencias
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.mesa_schema import (
    MesaCreate,
    MesaUpdate,
    MesaResponse,
)
from app.schemas.reserva_schema import ReservaResponse
from app.services import mesa_service, reserva_service

router = APIRouter(prefix="/mesas", tags=["Mesas"])


# ── Mesa ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[MesaResponse])
async def listar_mesas(
    estado: str | None = Query(None),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await mesa_service.get_mesas(db, estado=estado, solo_activas=solo_activas)


@router.get("/{id_mesa}", response_model=MesaResponse)
async def obtener_mesa(
    id_mesa: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await mesa_service.get_mesa(db, id_mesa)


@router.post("", response_model=MesaResponse, status_code=status.HTTP_201_CREATED)
async def crear_mesa(
    data: MesaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await mesa_service.create_mesa(db, data)


@router.patch("/{id_mesa}", response_model=MesaResponse)
async def actualizar_mesa(
    id_mesa: int,
    data: MesaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await mesa_service.update_mesa(db, id_mesa, data)


@router.patch("/{id_mesa}/estado", response_model=MesaResponse)
async def cambiar_estado_mesa(
    id_mesa: int,
    nuevo_estado: str = Query(..., description="disponible | ocupada | reservada"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("cajero", "mesero", "administrador")),
):
    return await mesa_service.cambiar_estado_mesa(db, id_mesa, nuevo_estado)


# ── Reservas por mesa (solo lectura) ─────────────────────────────────────────

@router.get("/{id_mesa}/reservas", response_model=list[ReservaResponse])
async def listar_reservas_de_mesa(
    id_mesa: int,
    estado: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Convenience endpoint — delegates to reserva_service."""
    return await reserva_service.get_reservas(db, id_mesa=id_mesa, estado=estado)