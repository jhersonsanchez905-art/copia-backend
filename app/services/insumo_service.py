"""
insumo_service.py
Lógica de negocio para gestión de insumos, subrecetas e ingredientes de subreceta.
Autor: Ivan Ospino
Issue: #19
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories import insumo_repo
from app.schemas.insumo_schema import InsumoCreate, InsumoUpdate, SubrecetaCreate, SubrecetaUpdate, SubrecetaIngredienteCreate, SubrecetaIngredienteUpdate


# ── Insumo ────────────────────────────────────────────────────────────────────

def get_insumo(db: Session, id_insumo: int):
    insumo = insumo_repo.get_insumo(db, id_insumo)
    if not insumo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insumo no encontrado")
    return insumo


def get_insumos(db: Session, skip: int = 0, limit: int = 100):
    return insumo_repo.get_insumos(db, skip, limit)


def create_insumo(db: Session, data: InsumoCreate):
    return insumo_repo.create_insumo(db, data)


def update_insumo(db: Session, id_insumo: int, data: InsumoUpdate):
    insumo = insumo_repo.update_insumo(db, id_insumo, data)
    if not insumo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insumo no encontrado")
    return insumo


def delete_insumo(db: Session, id_insumo: int):
    insumo = insumo_repo.delete_insumo(db, id_insumo)
    if not insumo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insumo no encontrado")
    return insumo


# ── Subreceta ─────────────────────────────────────────────────────────────────

def get_subreceta(db: Session, id_subreceta: int):
    subreceta = insumo_repo.get_subreceta(db, id_subreceta)
    if not subreceta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subreceta no encontrada")
    return subreceta


def get_subrecetas(db: Session, skip: int = 0, limit: int = 100):
    return insumo_repo.get_subrecetas(db, skip, limit)


def create_subreceta(db: Session, data: SubrecetaCreate):
    return insumo_repo.create_subreceta(db, data)


def update_subreceta(db: Session, id_subreceta: int, data: SubrecetaUpdate):
    subreceta = insumo_repo.update_subreceta(db, id_subreceta, data)
    if not subreceta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subreceta no encontrada")
    return subreceta


def delete_subreceta(db: Session, id_subreceta: int):
    subreceta = insumo_repo.delete_subreceta(db, id_subreceta)
    if not subreceta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subreceta no encontrada")
    return subreceta


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

def get_ingredientes_by_subreceta(db: Session, id_subreceta: int):
    get_subreceta(db, id_subreceta)
    return insumo_repo.get_ingredientes_by_subreceta(db, id_subreceta)


def create_ingrediente(db: Session, data: SubrecetaIngredienteCreate):
    get_subreceta(db, data.id_subreceta)
    existing = insumo_repo.get_ingrediente(db, data.id_subreceta, data.id_insumo)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El ingrediente ya existe en esta subreceta")
    return insumo_repo.create_ingrediente(db, data)


def update_ingrediente(db: Session, id_subreceta: int, id_insumo: int, data: SubrecetaIngredienteUpdate):
    ingrediente = insumo_repo.update_ingrediente(db, id_subreceta, id_insumo, data)
    if not ingrediente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingrediente no encontrado")
    return ingrediente


def delete_ingrediente(db: Session, id_subreceta: int, id_insumo: int):
    ingrediente = insumo_repo.delete_ingrediente(db, id_subreceta, id_insumo)
    if not ingrediente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingrediente no encontrado")
    return ingrediente