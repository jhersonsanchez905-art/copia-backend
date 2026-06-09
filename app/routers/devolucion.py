"""
devolucion.py (router)
Endpoints for Devolucion (returns).
States: pendiente → aprobada | rechazada

<<<<<<< HEAD
Author: Jherson
=======
Author: SebasValero12
>>>>>>> 37ef0cb (feat: complete pedido, caja, and devolucion flows)
Issue: #40
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.devolucion_schema import DevolucionCreate, DevolucionResponse
from app.services import devolucion_service

router = APIRouter(prefix="/devoluciones", tags=["Devoluciones"])


@router.get("", response_model=list[DevolucionResponse])
async def listar_devoluciones(
    estado: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await devolucion_service.get_devoluciones(db, estado=estado)


@router.get("/{id_devolucion}", response_model=DevolucionResponse)
async def obtener_devolucion(
    id_devolucion: int, db: AsyncSession = Depends(get_db)
):
    return await devolucion_service.get_devolucion(db, id_devolucion)


@router.post(
    "", response_model=DevolucionResponse, status_code=status.HTTP_201_CREATED
)
async def crear_devolucion(
    data: DevolucionCreate, db: AsyncSession = Depends(get_db)
):
    return await devolucion_service.crear_devolucion(db, data)


@router.patch("/{id_devolucion}/aprobar", response_model=DevolucionResponse)
async def aprobar_devolucion(
    id_devolucion: int, db: AsyncSession = Depends(get_db)
):
    """Approve a return (admin only). Reintegrates stock if flagged."""
    id_usuario = 1  # TODO: extract from Clerk token
    return await devolucion_service.aprobar_devolucion(
        db, id_devolucion, id_usuario
    )


@router.patch("/{id_devolucion}/rechazar", response_model=DevolucionResponse)
async def rechazar_devolucion(
    id_devolucion: int, db: AsyncSession = Depends(get_db)
):
    """Reject a return (admin only). Does NOT affect inventory."""
    id_usuario = 1  # TODO: extract from Clerk token
    return await devolucion_service.rechazar_devolucion(
        db, id_devolucion, id_usuario
    )
