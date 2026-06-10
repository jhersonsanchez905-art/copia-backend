"""
inventario_repo.py
Async repository for MovimientoInventario and Alerta.
Stock updates go through stock_repo.py.
AjusteInventario has its own repo.
"""
import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventario import MovimientoInventario, Alerta


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── MovimientoInventario ──────────────────────────────────────────────────────

async def create_movimiento(
    db: AsyncSession, movimiento: MovimientoInventario
) -> MovimientoInventario:
    db.add(movimiento)
    await db.flush()
    await db.refresh(movimiento)
    return movimiento


async def get_movimiento_by_id(
    db: AsyncSession, id_movimiento: int
) -> MovimientoInventario | None:
    return await db.get(MovimientoInventario, id_movimiento)


async def get_movimientos_by_insumo(
    db: AsyncSession, id_insumo: int
) -> list[MovimientoInventario]:
    result = await db.execute(
        select(MovimientoInventario)
        .where(MovimientoInventario.id_insumo == id_insumo)
        .order_by(MovimientoInventario.fecha.desc())
    )
    return list(result.scalars().all())


# ── Alerta ────────────────────────────────────────────────────────────────────

async def get_alerta_activa_by_insumo(
    db: AsyncSession, id_insumo: int
) -> Alerta | None:
    result = await db.execute(
        select(Alerta).where(
            Alerta.id_insumo == id_insumo,
            Alerta.estado == "activa",
        )
    )
    return result.scalar_one_or_none()


async def create_alerta(db: AsyncSession, alerta: Alerta) -> Alerta:
    db.add(alerta)
    await db.flush()
    await db.refresh(alerta)
    return alerta


async def get_alertas_activas(db: AsyncSession) -> list[Alerta]:
    result = await db.execute(
        select(Alerta).where(Alerta.estado == "activa")
    )
    return list(result.scalars().all())


async def resolver_alerta(db: AsyncSession, id_insumo: int) -> None:
    await db.execute(
        update(Alerta)
        .where(Alerta.id_insumo == id_insumo, Alerta.estado == "activa")
        .values(estado="resuelta", fecha_resolucion=_now())
    )
