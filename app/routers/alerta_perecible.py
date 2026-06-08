"""
alerta_perecible.py
Endpoints de consulta y resolución de alertas de perecibles.
Las alertas son generadas por un proceso automático, no por la API.
Autor: Ivan Ospino
Issue: #21
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.alerta_perecible_schema import (
    AlertaPerecibleResponse,
    EstadoAlertaPerecibleEnum,
)
from app.services import alerta_perecible_service

router = APIRouter(prefix="/alertas-perecibles", tags=["Alertas Perecibles"])


@router.get("", response_model=list[AlertaPerecibleResponse])
async def listar_alertas_perecibles(
    estado: EstadoAlertaPerecibleEnum | None = Query(None),
    id_insumo: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await alerta_perecible_service.get_alertas_perecibles(
        db,
        estado=estado.value if estado else None,
        id_insumo=id_insumo,
    )


@router.get("/{id_alerta}", response_model=AlertaPerecibleResponse)
async def obtener_alerta_perecible(
    id_alerta: int, db: AsyncSession = Depends(get_db)
):
    return await alerta_perecible_service.get_alerta_perecible(db, id_alerta)


@router.patch("/{id_alerta}/resolver", response_model=AlertaPerecibleResponse)
async def resolver_alerta_perecible(
    id_alerta: int, db: AsyncSession = Depends(get_db)
):
    return await alerta_perecible_service.resolver_alerta_perecible(db, id_alerta)