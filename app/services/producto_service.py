"""
producto_service.py
Lógica de negocio para Producto.
Autor SebastianValero12
Issue: #40
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.producto import Producto
from app.repositories import producto_repo
from app.schemas.producto_schema import ProductoCreate, ProductoUpdate


async def listar_productos(
    db: AsyncSession,
    *,
    solo_activos: bool = True,
    id_categoria: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    items = await producto_repo.get_all(
        db,
        solo_activos=solo_activos,
        id_categoria=id_categoria,
        skip=skip,
        limit=limit,
    )
    total = await producto_repo.count(
        db, solo_activos=solo_activos, id_categoria=id_categoria
    )
    return {"items": items, "total": total}


async def obtener_producto(db: AsyncSession, producto_id: int) -> Producto:
    producto = await producto_repo.get_by_id(db, producto_id)
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado",
        )
    return producto


async def crear_producto(
    db: AsyncSession, payload: ProductoCreate
) -> Producto:
    producto = Producto(**payload.model_dump())
    producto = await producto_repo.create(db, producto)
    await db.commit()
    return producto


async def actualizar_producto(
    db: AsyncSession, producto_id: int, payload: ProductoUpdate
) -> Producto:
    producto = await obtener_producto(db, producto_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron campos para actualizar",
        )
    producto = await producto_repo.update(db, producto, data)
    await db.commit()
    return producto


async def eliminar_producto(db: AsyncSession, producto_id: int) -> None:
    producto = await obtener_producto(db, producto_id)
    await producto_repo.delete(db, producto)
    await db.commit()