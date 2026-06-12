"""
orden_compra_repo.py
Repositorio de acceso a datos para órdenes de compra y sus líneas de detalle.
Autor: Ivan Ospino
Issue: #20
"""

from sqlalchemy.orm import Session
from app.models.orden_compra import OrdenCompra, OrdenCompraDetalle
from app.schemas.orden_compra_schema import OrdenCompraCreate, OrdenCompraUpdate, OrdenCompraDetalleCreate, OrdenCompraDetalleUpdate


# ── OrdenCompra ───────────────────────────────────────────────────────────────

def get_orden_compra(db: Session, id_orden_compra: int):
    return db.query(OrdenCompra).filter(OrdenCompra.id_orden_compra == id_orden_compra).first()


def get_ordenes_compra(db: Session, skip: int = 0, limit: int = 100):
    return db.query(OrdenCompra).offset(skip).limit(limit).all()


def create_orden_compra(db: Session, data: OrdenCompraCreate):
    detalles_data = data.detalles or []
    orden_data = data.model_dump(exclude={"detalles"})
    orden = OrdenCompra(**orden_data)
    db.add(orden)
    db.flush()
    for detalle in detalles_data:
        db.add(OrdenCompraDetalle(id_orden_compra=orden.id_orden_compra, **detalle.model_dump()))
    db.commit()
    db.refresh(orden)
    return orden


def update_orden_compra(db: Session, id_orden_compra: int, data: OrdenCompraUpdate):
    orden = get_orden_compra(db, id_orden_compra)
    if not orden:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(orden, field, value)
    db.commit()
    db.refresh(orden)
    return orden


def delete_orden_compra(db: Session, id_orden_compra: int):
    orden = get_orden_compra(db, id_orden_compra)
    if not orden:
        return None
    db.delete(orden)
    db.commit()
    return orden


# ── OrdenCompraDetalle ────────────────────────────────────────────────────────

def get_detalle(db: Session, id_detalle: int):
    return db.query(OrdenCompraDetalle).filter(OrdenCompraDetalle.id_detalle == id_detalle).first()


def get_detalles_by_orden(db: Session, id_orden_compra: int):
    return db.query(OrdenCompraDetalle).filter(
        OrdenCompraDetalle.id_orden_compra == id_orden_compra
    ).all()


def create_detalle(db: Session, id_orden_compra: int, data: OrdenCompraDetalleCreate):
    detalle = OrdenCompraDetalle(id_orden_compra=id_orden_compra, **data.model_dump())
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return detalle


def update_detalle(db: Session, id_detalle: int, data: OrdenCompraDetalleUpdate):
    detalle = get_detalle(db, id_detalle)
    if not detalle:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(detalle, field, value)
    db.commit()
    db.refresh(detalle)
    return detalle


def delete_detalle(db: Session, id_detalle: int):
    detalle = get_detalle(db, id_detalle)
    if not detalle:
        return None
    db.delete(detalle)
    db.commit()
    return detalle