"""
app/routers/proveedor.py
REST endpoints for suppliers and supplier-input relationships.
Author: charlykj
Issue: #38
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.proveedor_service import ProveedorService, InsumoProveedorService
from app.schemas.proveedor_schema import (
    ProveedorCreate, ProveedorUpdate, ProveedorOut,
    InsumoProveedorCreate, InsumoProveedorOut
)

router = APIRouter(tags=["Proveedores"])

# --- Proveedores ---
@router.get("/proveedores", response_model=List[ProveedorOut])
async def listar_proveedores(db: AsyncSession = Depends(get_db)):
    return await ProveedorService(db).listar()

@router.get("/proveedores/{id_proveedor}", response_model=ProveedorOut)
async def obtener_proveedor(id_proveedor: int, db: AsyncSession = Depends(get_db)):
    obj = await ProveedorService(db).obtener(id_proveedor)
    if not obj:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return obj

@router.post("/proveedores", response_model=ProveedorOut, status_code=201)
async def crear_proveedor(data: ProveedorCreate, db: AsyncSession = Depends(get_db)):
    return await ProveedorService(db).crear(data)

@router.put("/proveedores/{id_proveedor}", response_model=ProveedorOut)
async def actualizar_proveedor(id_proveedor: int, data: ProveedorUpdate, db: AsyncSession = Depends(get_db)):
    obj = await ProveedorService(db).actualizar(id_proveedor, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return obj

@router.delete("/proveedores/{id_proveedor}", status_code=204)
async def eliminar_proveedor(id_proveedor: int, db: AsyncSession = Depends(get_db)):
    if not await ProveedorService(db).eliminar(id_proveedor):
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

# --- Insumos Proveedor ---
@router.get("/insumos-proveedor", response_model=List[InsumoProveedorOut])
async def listar_insumos_proveedor(db: AsyncSession = Depends(get_db)):
    return await InsumoProveedorService(db).listar()

@router.get("/insumos-proveedor/{id_insumo_proveedor}", response_model=InsumoProveedorOut)
async def obtener_insumo_proveedor(id_insumo_proveedor: int, db: AsyncSession = Depends(get_db)):
    obj = await InsumoProveedorService(db).obtener(id_insumo_proveedor)
    if not obj:
        raise HTTPException(status_code=404, detail="Insumo proveedor no encontrado")
    return obj

@router.post("/insumos-proveedor", response_model=InsumoProveedorOut, status_code=201)
async def crear_insumo_proveedor(data: InsumoProveedorCreate, db: AsyncSession = Depends(get_db)):
    return await InsumoProveedorService(db).crear(data)

@router.delete("/insumos-proveedor/{id_insumo_proveedor}", status_code=204)
async def eliminar_insumo_proveedor(id_insumo_proveedor: int, db: AsyncSession = Depends(get_db)):
    if not await InsumoProveedorService(db).eliminar(id_insumo_proveedor):
        raise HTTPException(status_code=404, detail="Insumo proveedor no encontrado")