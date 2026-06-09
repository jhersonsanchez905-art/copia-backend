"""
stock.py (router)
Read-only endpoints for Stock semaforo status.
Stock is updated automatically — never via direct API call.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.stock_schema import SemaforoEnum, StockResponse
from app.services import stock_service

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("", response_model=list[StockResponse], summary="Listar stock con filtro de semaforo")
async def listar_stock(
    semaforo: SemaforoEnum | None = Query(None, description="verde | amarillo | rojo"),
    db: AsyncSession = Depends(get_db),
):
    return await stock_service.get_all_stocks(db, semaforo=semaforo.value if semaforo else None)


@router.get(
    "/insumo/{id_insumo}",
    response_model=StockResponse,
    summary="Obtener stock de un insumo específico",
)
async def get_stock_insumo(id_insumo: int, db: AsyncSession = Depends(get_db)):
    return await stock_service.get_stock_by_insumo(db, id_insumo)
