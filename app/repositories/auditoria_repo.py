"""
auditoria_repo.py
Async repository for Auditoria (append-only audit log).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auditoria import Auditoria


async def create_auditoria(db: AsyncSession, auditoria: Auditoria) -> Auditoria:
    db.add(auditoria)
    await db.flush()
    return auditoria


async def get_auditorias(
    db: AsyncSession,
    entidad: str | None = None,
    id_registro: int | None = None,
    accion: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Auditoria]:
    query = select(Auditoria)
    if entidad:
        query = query.where(Auditoria.entidad == entidad)
    if id_registro is not None:
        query = query.where(Auditoria.id_registro == id_registro)
    if accion:
        query = query.where(Auditoria.accion == accion)
    query = query.order_by(Auditoria.fecha.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
