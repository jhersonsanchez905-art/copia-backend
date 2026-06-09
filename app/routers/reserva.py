"""
reserva.py (router)
Endpoints for Reserva management with state machine enforcement.
Confirm and cancel are restricted to Administrador role.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
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
):
    return await reserva_service.get_reservas(
        db,
        id_mesa=id_mesa,
        estado=estado.value if estado else None,
        skip=skip,
        limit=limit,
    )


@router.get("/{id_reserva}", response_model=ReservaResponse)
async def obtener_reserva(id_reserva: int, db: AsyncSession = Depends(get_db)):
    return await reserva_service.get_reserva(db, id_reserva)


@router.post("", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
async def crear_reserva(data: ReservaCreate, db: AsyncSession = Depends(get_db)):
    # TODO: extract id_usuario from Clerk token
    id_usuario = 1
    return await reserva_service.crear_reserva(db, data, id_usuario)


@router.patch("/{id_reserva}", response_model=ReservaResponse)
async def actualizar_reserva(
    id_reserva: int, data: ReservaUpdate, db: AsyncSession = Depends(get_db)
):
    return await reserva_service.actualizar_reserva(db, id_reserva, data)


@router.patch(
    "/{id_reserva}/confirmar",
    response_model=ReservaResponse,
    summary="Confirmar reserva (solo Administrador)",
)
async def confirmar_reserva(id_reserva: int, db: AsyncSession = Depends(get_db)):
    # TODO: extract id_usuario and validate Administrador role from Clerk token
    id_usuario = 1
    es_administrador = True  # placeholder until Clerk auth is wired
    return await reserva_service.confirmar_reserva(
        db, id_reserva, id_usuario, es_administrador
    )


@router.patch(
    "/{id_reserva}/cancelar",
    response_model=ReservaResponse,
    summary="Cancelar reserva (solo Administrador)",
)
async def cancelar_reserva(id_reserva: int, db: AsyncSession = Depends(get_db)):
    # TODO: extract id_usuario and validate Administrador role from Clerk token
    id_usuario = 1
    es_administrador = True  # placeholder until Clerk auth is wired
    return await reserva_service.cancelar_reserva(
        db, id_reserva, id_usuario, es_administrador
    )


@router.patch(
    "/{id_reserva}/completar",
    response_model=ReservaResponse,
    summary="Marcar como completada cuando el cliente llega (mesa pasa a ocupada)",
)
async def completar_reserva(id_reserva: int, db: AsyncSession = Depends(get_db)):
    return await reserva_service.completar_reserva(db, id_reserva)
