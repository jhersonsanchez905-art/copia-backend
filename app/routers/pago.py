"""
pago.py (router)
HTTP endpoints for payment validation (RF-012).
Delegates business logic to pago_service.

Endpoints:
    PATCH  /api/v1/pagos/{id_pago}/validar   approve or reject a pending payment

Author: Iván Ospino / SebastianValero12
Issue: RF-012 — fix/reservas-transferencias
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.roles import require_rol
from app.models.catalogo import Usuario
from app.schemas.pago_schema import PagoDetalleResponse, ValidarPagoRequest
from app.services import pago_service

router = APIRouter()


@router.patch(
    "/{id_pago}/validar",
    response_model=PagoDetalleResponse,
    summary="Validar pago de transferencia (aprobar o rechazar)",
)
async def validar_pago(
    id_pago: int,
    data: ValidarPagoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_rol("administrador")),
):
    """Approve or reject a pending transfer payment.

    Only payments with a método de pago that requires comprobante
    can be validated. The validator's identity is taken from the
    authenticated user automatically.
    """
    return await pago_service.validar_pago(
        db,
        id_pago=id_pago,
        data=data,
        id_usuario_validacion=current_user.id_usuario,
    )