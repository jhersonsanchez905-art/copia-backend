"""
stock.py
Endpoints de consulta de stock con semáforo. No permite modificar stock directamente.
Autor: Ivan Ospino
Issue: #21
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.stock_schema import StockResponse
from app.services import stock_service

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("", response_model=list[StockResponse])
async def listar_stock(db: AsyncSession = Depends(get_db)):
    return await stock_service.get_all_stocks(db)


@router.get("/criticos", response_model=list[StockResponse])
async def listar_stock_criticos(db: AsyncSession = Depends(get_db)):
    return await stock_service.get_all_stocks(db, semaforo="rojo")


@router.get("/vigilancia", response_model=list[StockResponse])
async def listar_stock_vigilancia(db: AsyncSession = Depends(get_db)):
    return await stock_service.get_all_stocks(db, semaforo="amarillo")


@router.get("/{id_insumo}", response_model=StockResponse)
async def get_stock_insumo(id_insumo: int, db: AsyncSession = Depends(get_db)):
    return await stock_service.get_stock_by_insumo(db, id_insumo)