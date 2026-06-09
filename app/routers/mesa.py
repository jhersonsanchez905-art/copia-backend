"""
mesa.py (router)
Endpoints for Mesa and Reserva management with state machine enforcement.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.mesa_schema import (
    MesaCreate,
    MesaUpdate,
    MesaResponse,
    ReservaCreate,
    ReservaResponse,
)
from app.services import mesa_service

router = APIRouter(prefix="/mesas", tags=["Mesas y Reservas"])


# ── Mesa ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[MesaResponse])
async def listar_mesas(
    estado: str | None = Query(None),
    solo_activas: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    return await mesa_service.get_mesas(db, estado=estado, solo_activas=solo_activas)


@router.get("/{id_mesa}", response_model=MesaResponse)
async def obtener_mesa(id_mesa: int, db: AsyncSession = Depends(get_db)):
    return await mesa_service.get_mesa(db, id_mesa)


@router.post("", response_model=MesaResponse, status_code=status.HTTP_201_CREATED)
async def crear_mesa(data: MesaCreate, db: AsyncSession = Depends(get_db)):
    return await mesa_service.create_mesa(db, data)


@router.patch("/{id_mesa}", response_model=MesaResponse)
async def actualizar_mesa(
    id_mesa: int, data: MesaUpdate, db: AsyncSession = Depends(get_db)
):
    return await mesa_service.update_mesa(db, id_mesa, data)


@router.patch("/{id_mesa}/estado", response_model=MesaResponse)
async def cambiar_estado_mesa(
    id_mesa: int,
    nuevo_estado: str = Query(..., description="disponible | ocupada | reservada"),
    db: AsyncSession = Depends(get_db),
):
    return await mesa_service.cambiar_estado_mesa(db, id_mesa, nuevo_estado)


<<<<<<< HEAD
=======
@router.put("/{id_mesa}", response_model=MesaResponse)
async def editar_mesa(
    id_mesa: int, data: MesaUpdate, db: AsyncSession = Depends(get_db)
):
    return await mesa_service.update_mesa(db, id_mesa, data)


@router.delete("/{id_mesa}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mesa(id_mesa: int, db: AsyncSession = Depends(get_db)):
    return await mesa_service.delete_mesa(db, id_mesa)


>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
# ── Reserva ───────────────────────────────────────────────────────────────────

@router.get("/{id_mesa}/reservas", response_model=list[ReservaResponse])
async def listar_reservas_de_mesa(
    id_mesa: int,
    estado: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await mesa_service.get_reservas(db, id_mesa=id_mesa, estado=estado)


@router.get("/reservas/all", response_model=list[ReservaResponse])
async def listar_reservas(
    estado: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await mesa_service.get_reservas(db, estado=estado)


@router.post(
    "/reservas",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_reserva(data: ReservaCreate, db: AsyncSession = Depends(get_db)):
<<<<<<< HEAD
    # TODO: extract id_usuario from Clerk token
=======
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
    id_usuario = 1
    return await mesa_service.create_reserva(db, data, id_usuario)


@router.patch("/reservas/{id_reserva}/estado", response_model=ReservaResponse)
async def cambiar_estado_reserva(
    id_reserva: int,
    nuevo_estado: str = Query(..., description="confirmada | cancelada | completada"),
    db: AsyncSession = Depends(get_db),
):
<<<<<<< HEAD
    return await mesa_service.cambiar_estado_reserva(db, id_reserva, nuevo_estado)
=======
    return await mesa_service.cambiar_estado_reserva(db, id_reserva, nuevo_estado)
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
