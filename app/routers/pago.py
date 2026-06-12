"""
app/routers/pago.py

HTTP endpoint for payment validation (RF-012).
Delegates business logic to venta_service.

Endpoints:
    PATCH  /api/v1/pagos/{id_pago}/validar   approve or reject a pending payment

Author: Iván Ospino
Issue: RF-012
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import venta_service
from app.schemas.venta_schema import ValidarPagoRequest, PagoDetalleResponse

router = APIRouter()


@router.patch("/{id_pago}/validar", response_model=PagoDetalleResponse)
async def validar_pago(
    id_pago: int,
    data: ValidarPagoRequest,
    db: AsyncSession = Depends(get_db),
):

    return await venta_service.validar_pago(id_pago, data, db)
