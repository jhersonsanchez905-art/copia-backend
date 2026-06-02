"""
insumo.py
Endpoints CRUD para insumos, subrecetas e ingredientes de subreceta.
Autor: Ivan Ospino
Issue: #19
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import insumo_service
from app.schemas.insumo_schema import (
    InsumoCreate, InsumoUpdate, InsumoOut,
    SubrecetaCreate, SubrecetaUpdate, SubrecetaOut,
    SubrecetaIngredienteCreate, SubrecetaIngredienteUpdate, SubrecetaIngredienteOut,
)

router = APIRouter()


# ── Insumo ────────────────────────────────────────────────────────────────────

@router.get("/insumos", response_model=List[InsumoOut], tags=["Insumos"])
def listar_insumos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return insumo_service.get_insumos(db, skip, limit)


@router.get("/insumos/{id_insumo}", response_model=InsumoOut, tags=["Insumos"])
def obtener_insumo(id_insumo: int, db: Session = Depends(get_db)):
    return insumo_service.get_insumo(db, id_insumo)


@router.post("/insumos", response_model=InsumoOut, status_code=201, tags=["Insumos"])
def crear_insumo(data: InsumoCreate, db: Session = Depends(get_db)):
    return insumo_service.create_insumo(db, data)


@router.patch("/insumos/{id_insumo}", response_model=InsumoOut, tags=["Insumos"])
def actualizar_insumo(id_insumo: int, data: InsumoUpdate, db: Session = Depends(get_db)):
    return insumo_service.update_insumo(db, id_insumo, data)


@router.delete("/insumos/{id_insumo}", response_model=InsumoOut, tags=["Insumos"])
def eliminar_insumo(id_insumo: int, db: Session = Depends(get_db)):
    return insumo_service.delete_insumo(db, id_insumo)


# ── Subreceta ─────────────────────────────────────────────────────────────────

@router.get("/subrecetas", response_model=List[SubrecetaOut], tags=["Subrecetas"])
def listar_subrecetas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return insumo_service.get_subrecetas(db, skip, limit)


@router.get("/subrecetas/{id_subreceta}", response_model=SubrecetaOut, tags=["Subrecetas"])
def obtener_subreceta(id_subreceta: int, db: Session = Depends(get_db)):
    return insumo_service.get_subreceta(db, id_subreceta)


@router.post("/subrecetas", response_model=SubrecetaOut, status_code=201, tags=["Subrecetas"])
def crear_subreceta(data: SubrecetaCreate, db: Session = Depends(get_db)):
    return insumo_service.create_subreceta(db, data)


@router.patch("/subrecetas/{id_subreceta}", response_model=SubrecetaOut, tags=["Subrecetas"])
def actualizar_subreceta(id_subreceta: int, data: SubrecetaUpdate, db: Session = Depends(get_db)):
    return insumo_service.update_subreceta(db, id_subreceta, data)


@router.delete("/subrecetas/{id_subreceta}", response_model=SubrecetaOut, tags=["Subrecetas"])
def eliminar_subreceta(id_subreceta: int, db: Session = Depends(get_db)):
    return insumo_service.delete_subreceta(db, id_subreceta)


# ── SubrecetaIngrediente ──────────────────────────────────────────────────────

@router.get("/subrecetas/{id_subreceta}/ingredientes", response_model=List[SubrecetaIngredienteOut], tags=["Subrecetas"])
def listar_ingredientes(id_subreceta: int, db: Session = Depends(get_db)):
    return insumo_service.get_ingredientes_by_subreceta(db, id_subreceta)


@router.post("/subrecetas/ingredientes", response_model=SubrecetaIngredienteOut, status_code=201, tags=["Subrecetas"])
def crear_ingrediente(data: SubrecetaIngredienteCreate, db: Session = Depends(get_db)):
    return insumo_service.create_ingrediente(db, data)


@router.patch("/subrecetas/{id_subreceta}/ingredientes/{id_insumo}", response_model=SubrecetaIngredienteOut, tags=["Subrecetas"])
def actualizar_ingrediente(id_subreceta: int, id_insumo: int, data: SubrecetaIngredienteUpdate, db: Session = Depends(get_db)):
    return insumo_service.update_ingrediente(db, id_subreceta, id_insumo, data)


@router.delete("/subrecetas/{id_subreceta}/ingredientes/{id_insumo}", response_model=SubrecetaIngredienteOut, tags=["Subrecetas"])
def eliminar_ingrediente(id_subreceta: int, id_insumo: int, db: Session = Depends(get_db)):
    return insumo_service.delete_ingrediente(db, id_subreceta, id_insumo)   