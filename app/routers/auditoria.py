"""
auditoria.py (router)
Read-only endpoints for Auditoria records.
Records are written automatically by AuditoriaMiddleware.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auditoria_schema import AccionEnum, AuditoriaResponse
from app.services import auditoria_service

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("", response_model=list[AuditoriaResponse])
async def listar_auditoria(
    entidad: str | None = Query(None, description="Nombre de la entidad, ej: venta"),
    id_registro: int | None = Query(None),
    accion: AccionEnum | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await auditoria_service.get_auditorias(
        db,
        entidad=entidad,
        id_registro=id_registro,
        accion=accion.value if accion else None,
        skip=skip,
        limit=limit,
    )
