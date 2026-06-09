"""
orden_compra_repo.py
Repositorio async para OrdenCompra y OrdenCompraDetalle.
Usa AsyncSession + select() (SQLAlchemy 2.x). Sin session.query().
Autor: Ivan Ospino
Issue: #21
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.orden_compra import OrdenCompra, OrdenCompraDetalle
from app.schemas.orden_compra_schema import OrdenCompraCreate


# ── OrdenCompra ───────────────────────────────────────────────────────────────

async def get_orden_compra_by_id(
    db: AsyncSession, id_orden_compra: int
) -> OrdenCompra | None:
    result = await db.execute(
        select(OrdenCompra)
        .options(selectinload(OrdenCompra.detalles))
        .where(OrdenCompra.id_orden_compra == id_orden_compra)
    )
    return result.scalar_one_or_none()


async def get_ordenes_compra(
    db: AsyncSession,
    estado: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[OrdenCompra]:
    query = select(OrdenCompra).options(selectinload(OrdenCompra.detalles))
    if estado:
        query = query.where(OrdenCompra.estado == estado)
    query = query.order_by(OrdenCompra.fecha_creacion.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_orden_compra(
    db: AsyncSession, data: OrdenCompraCreate
) -> OrdenCompra:
    detalles_data = data.detalles or []
    orden_data = data.model_dump(exclude={"detalles"})
    orden = OrdenCompra(**orden_data)
    db.add(orden)
    await db.flush()

    for d in detalles_data:
        detalle = OrdenCompraDetalle(
            id_orden_compra=orden.id_orden_compra,
            **d.model_dump(),
        )
        db.add(detalle)

    await db.flush()
    await db.refresh(orden)
    return orden


async def update_orden_compra(
    db: AsyncSession, orden: OrdenCompra, data: dict
) -> OrdenCompra:
    for key, value in data.items():
        setattr(orden, key, value)
    await db.flush()
    await db.refresh(orden)
    return orden


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

async def get_detalle_by_insumo(
    db: AsyncSession, id_orden_compra: int, id_insumo: int
) -> OrdenCompraDetalle | None:
    result = await db.execute(
        select(OrdenCompraDetalle).where(
            OrdenCompraDetalle.id_orden_compra == id_orden_compra,
            OrdenCompraDetalle.id_insumo == id_insumo,
        )
    )
    return result.scalar_one_or_none()


async def update_detalle(
    db: AsyncSession, detalle: OrdenCompraDetalle, data: dict
) -> OrdenCompraDetalle:
    for key, value in data.items():
        setattr(detalle, key, value)
    await db.flush()
    await db.refresh(detalle)
    return detalle