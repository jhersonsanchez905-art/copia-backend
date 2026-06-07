"""
alerta_perecible_service.py
Lógica de negocio para alertas de perecibles.
Las alertas son generadas por un proceso automático, nunca por llamada directa a la API.
Autor: Ivan Ospino
Issue: #21
"""
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.alerta_perecible import AlertaPerecible
from app.repositories import alerta_perecible_repo


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def get_alerta_perecible(db: AsyncSession, id_alerta: int) -> AlertaPerecible:
    alerta = await alerta_perecible_repo.get_alerta_perecible_by_id(db, id_alerta)
    if not alerta:
        raise MajesaError(f"AlertaPerecible {id_alerta} no encontrada", 404)
    return alerta


async def get_alertas_perecibles(
    db: AsyncSession,
    estado: str | None = None,
    id_insumo: int | None = None,
) -> list[AlertaPerecible]:
    return await alerta_perecible_repo.get_alertas_perecibles(
        db, estado=estado, id_insumo=id_insumo
    )


async def resolver_alerta_perecible(
    db: AsyncSession, id_alerta: int
) -> AlertaPerecible:
    alerta = await get_alerta_perecible(db, id_alerta)
    if alerta.estado == "resuelta":
        raise MajesaError(
            f"La alerta {id_alerta} ya se encuentra resuelta", 400
        )
    alerta.estado = "resuelta"
    alerta.fecha_resolucion = _now()
    await db.flush()
    await db.commit()
    return alerta