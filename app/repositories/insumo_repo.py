"""
insumo_repo.py
Repositorio de acceso a datos para insumos, subrecetas e ingredientes de subreceta.
Autor: Ivan Ospino
Issue: #19
"""

from sqlalchemy.orm import Session
from app.models.insumo import Insumo, Subreceta, SubrecetaIngrediente
from app.schemas.insumo_schema import InsumoCreate, InsumoUpdate, SubrecetaCreate, SubrecetaUpdate, SubrecetaIngredienteCreate, SubrecetaIngredienteUpdate


# ── Insumo ────────────────────────────────────────────────────────────────────

def get_insumo(db: Session, id_insumo: int):
    return db.query(Insumo).filter(Insumo.id_insumo == id_insumo).first()


def get_insumos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Insumo).offset(skip).limit(limit).all()


def create_insumo(db: Session, data: InsumoCreate):
    insumo = Insumo(**data.model_dump())
    db.add(insumo)
    db.commit()
    db.refresh(insumo)
    return insumo


def update_insumo(db: Session, id_insumo: int, data: InsumoUpdate):
    insumo = get_insumo(db, id_insumo)
    if not insumo:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(insumo, field, value)
    db.commit()
    db.refresh(insumo)
    return insumo


def delete_insumo(db: Session, id_insumo: int):
    insumo = get_insumo(db, id_insumo)
    if not insumo:
        return None
    db.delete(insumo)
    db.commit()
    return insumo


# ── Subreceta ─────────────────────────────────────────────────────────────────

def get_subreceta(db: Session, id_subreceta: int):
    return db.query(Subreceta).filter(Subreceta.id_subreceta == id_subreceta).first()


def get_subrecetas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Subreceta).offset(skip).limit(limit).all()


def create_subreceta(db: Session, data: SubrecetaCreate):
    subreceta = Subreceta(**data.model_dump())
    db.add(subreceta)
    db.commit()
    db.refresh(subreceta)
    return subreceta


def update_subreceta(db: Session, id_subreceta: int, data: SubrecetaUpdate):
    subreceta = get_subreceta(db, id_subreceta)
    if not subreceta:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subreceta, field, value)
    db.commit()
    db.refresh(subreceta)
    return subreceta


def delete_subreceta(db: Session, id_subreceta: int):
    subreceta = get_subreceta(db, id_subreceta)
    if not subreceta:
        return None
    db.delete(subreceta)
    db.commit()
    return subreceta


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

def get_ingrediente(db: Session, id_subreceta: int, id_insumo: int):
    return db.query(SubrecetaIngrediente).filter(
        SubrecetaIngrediente.id_subreceta == id_subreceta,
        SubrecetaIngrediente.id_insumo == id_insumo
    ).first()


def get_ingredientes_by_subreceta(db: Session, id_subreceta: int):
    return db.query(SubrecetaIngrediente).filter(
        SubrecetaIngrediente.id_subreceta == id_subreceta
    ).all()


def create_ingrediente(db: Session, data: SubrecetaIngredienteCreate):
    ingrediente = SubrecetaIngrediente(**data.model_dump())
    db.add(ingrediente)
    db.commit()
    db.refresh(ingrediente)
    return ingrediente


def update_ingrediente(db: Session, id_subreceta: int, id_insumo: int, data: SubrecetaIngredienteUpdate):
    ingrediente = get_ingrediente(db, id_subreceta, id_insumo)
    if not ingrediente:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ingrediente, field, value)
    db.commit()
    db.refresh(ingrediente)
    return ingrediente


def delete_ingrediente(db: Session, id_subreceta: int, id_insumo: int):
    ingrediente = get_ingrediente(db, id_subreceta, id_insumo)
    if not ingrediente:
        return None
    db.delete(ingrediente)
    db.commit()
    return ingrediente