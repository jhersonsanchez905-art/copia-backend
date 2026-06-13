"""
orden_compra_repo.py
Async repository for OrdenCompra and OrdenCompraDetalle.
Uses SQLAlchemy 2.x select() syntax with AsyncSession.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.orden_compra import OrdenCompra, OrdenCompraDetalle


def _orden_options():
    return [selectinload(OrdenCompra.detalles)]


async def get_orden_compra(
    db: AsyncSession, id_orden_compra: int
) -> OrdenCompra | None:
    result = await db.execute(
        select(OrdenCompra)
        .options(*_orden_options())
        .where(OrdenCompra.id_orden_compra == id_orden_compra)
    )
    return result.scalar_one_or_none()


async def get_ordenes_compra(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[OrdenCompra]:
    result = await db.execute(
        select(OrdenCompra)
        .options(*_orden_options())
        .order_by(OrdenCompra.fecha_creacion.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_orden_compra(db: AsyncSession, data) -> OrdenCompra:
    detalles_data = data.detalles or []
    orden = OrdenCompra(**data.model_dump(exclude={"detalles"}))
    db.add(orden)
    await db.flush()
    for d in detalles_data:
        db.add(OrdenCompraDetalle(id_orden_compra=orden.id_orden_compra, **d.model_dump()))
    await db.flush()
    await db.refresh(orden)
    return orden


async def update_orden_compra(
    db: AsyncSession, orden: OrdenCompra, data: dict
) -> OrdenCompra:
    for field, value in data.items():
        setattr(orden, field, value)
    await db.flush()
    await db.refresh(orden)
    return orden


async def get_detalle(
    db: AsyncSession, id_detalle: int
) -> OrdenCompraDetalle | None:
    return await db.get(OrdenCompraDetalle, id_detalle)


async def get_detalles_by_orden(
    db: AsyncSession, id_orden_compra: int
) -> list[OrdenCompraDetalle]:
    result = await db.execute(
        select(OrdenCompraDetalle).where(
            OrdenCompraDetalle.id_orden_compra == id_orden_compra
        )
    )
    return list(result.scalars().all())


async def create_detalle(
    db: AsyncSession, id_orden_compra: int, data
) -> OrdenCompraDetalle:
    detalle = OrdenCompraDetalle(id_orden_compra=id_orden_compra, **data.model_dump())
    db.add(detalle)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def update_detalle(
    db: AsyncSession, detalle: OrdenCompraDetalle, data: dict
) -> OrdenCompraDetalle:
    for field, value in data.items():
        setattr(detalle, field, value)
    await db.flush()
    await db.refresh(detalle)
    return detalle


async def delete_detalle(
    db: AsyncSession, detalle: OrdenCompraDetalle
) -> None:
    await db.delete(detalle)
    await db.flush()
