"""
reserva.py (router)
Endpoints for Reserva management with state machine enforcement.
Confirm and cancel are restricted to Administrador role.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.reserva_schema import (
    EstadoReservaEnum,
    ReservaCreate,
    ReservaUpdate,
    ReservaResponse,
)
from app.services import reserva_service

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.get("", response_model=list[ReservaResponse])
async def listar_reservas(
    id_mesa: int | None = Query(None, description="Filtrar por mesa"),
    estado: EstadoReservaEnum | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await reserva_service.get_reservas(
        db,
        id_mesa=id_mesa,
        estado=estado.value if estado else None,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_reserva}", response_model=ReservaResponse)
async def obtener_reserva(
    id_reserva: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await reserva_service.get_reserva(db, id_reserva)


@router.post("", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
async def crear_reserva(
    data: ReservaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("mesero", "administrador")),
):
    return await reserva_service.crear_reserva(db, data, current_user.id_usuario)


@router.patch("/{id_reserva}", response_model=ReservaResponse)
async def actualizar_reserva(
    id_reserva: int,
    data: ReservaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await reserva_service.actualizar_reserva(db, id_reserva, data)


@router.patch(
    "/{id_reserva}/confirmar",
    response_model=ReservaResponse,
    summary="Confirmar reserva (solo Administrador)",
)
async def confirmar_reserva(
    id_reserva: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await reserva_service.confirmar_reserva(
        db, id_reserva, current_user.id_usuario, es_administrador=True
    )


@router.patch(
    "/{id_reserva}/cancelar",
    response_model=ReservaResponse,
    summary="Cancelar reserva (solo Administrador)",
)
async def cancelar_reserva(
    id_reserva: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await reserva_service.cancelar_reserva(
        db, id_reserva, current_user.id_usuario, es_administrador=True
    )


@router.patch(
    "/{id_reserva}/completar",
    response_model=ReservaResponse,
    summary="Marcar como completada cuando el cliente llega (mesa pasa a ocupada)",
)
async def completar_reserva(
    id_reserva: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    return await reserva_service.completar_reserva(db, id_reserva)
