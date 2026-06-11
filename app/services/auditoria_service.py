"""
auditoria_service.py
Read-only async service for Auditoria records.
Audit records are written by AuditoriaMiddleware, never via direct API.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auditoria import Auditoria
from app.repositories import auditoria_repo


async def get_auditorias(
    db: AsyncSession,
    entidad: str | None = None,
    id_registro: int | None = None,
    accion: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Auditoria]:
    return await auditoria_repo.get_auditorias(
        db,
        entidad=entidad,
        id_registro=id_registro,
        accion=accion,
        skip=skip,
        limit=limit,
    )
