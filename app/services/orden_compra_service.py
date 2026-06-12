"""
orden_compra_service.py
Lógica de negocio para gestión de órdenes de compra y sus líneas de detalle.
Autor: Ivan Ospino
Issue: #20
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories import orden_compra_repo
from app.schemas.orden_compra_schema import OrdenCompraCreate, OrdenCompraUpdate, OrdenCompraDetalleCreate, OrdenCompraDetalleUpdate
from app.models.orden_compra import EstadoOrdenCompra


# ── OrdenCompra ───────────────────────────────────────────────────────────────

def get_orden_compra(db: Session, id_orden_compra: int):
    orden = orden_compra_repo.get_orden_compra(db, id_orden_compra)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada")
    return orden


def get_ordenes_compra(db: Session, skip: int = 0, limit: int = 100):
    return orden_compra_repo.get_ordenes_compra(db, skip, limit)


def create_orden_compra(db: Session, data: OrdenCompraCreate):
    return orden_compra_repo.create_orden_compra(db, data)


def update_orden_compra(db: Session, id_orden_compra: int, data: OrdenCompraUpdate):
    orden = get_orden_compra(db, id_orden_compra)
    if orden.estado == EstadoOrdenCompra.CANCELADA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede modificar una orden cancelada")
    orden = orden_compra_repo.update_orden_compra(db, id_orden_compra, data)
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden de compra no encontrada")
    return orden


def delete_orden_compra(db: Session, id_orden_compra: int):
    orden = get_orden_compra(db, id_orden_compra)
    if orden.estado not in (EstadoOrdenCompra.BORRADOR, EstadoOrdenCompra.CANCELADA):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden eliminar órdenes en estado BORRADOR o CANCELADA")
    orden = orden_compra_repo.delete_orden_compra(db, id_orden_compra)
    return orden


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

def get_detalles_by_orden(db: Session, id_orden_compra: int):
    get_orden_compra(db, id_orden_compra)
    return orden_compra_repo.get_detalles_by_orden(db, id_orden_compra)


def create_detalle(db: Session, id_orden_compra: int, data: OrdenCompraDetalleCreate):
    orden = get_orden_compra(db, id_orden_compra)
    if orden.estado != EstadoOrdenCompra.BORRADOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden agregar detalles a órdenes en estado BORRADOR")
    return orden_compra_repo.create_detalle(db, id_orden_compra, data)


def update_detalle(db: Session, id_detalle: int, data: OrdenCompraDetalleUpdate):
    detalle = orden_compra_repo.update_detalle(db, id_detalle, data)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle no encontrado")
    return detalle


def delete_detalle(db: Session, id_detalle: int):
    detalle = orden_compra_repo.delete_detalle(db, id_detalle)
    if not detalle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle no encontrado")
    return detalle