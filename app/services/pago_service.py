"""
pago_service.py
Async business logic for payment validation (RF-012).

State machine:
  pendiente → aprobado  (transfer receipt approved)
  pendiente → rechazado (transfer receipt rejected)
  aprobado  → (terminal)
  rechazado → (terminal)

Only payments whose método de pago requires a comprobante can be validated.

Author: SebastianValero12
Issue: RF-012 — fix/reservas-transferencias
"""
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError
from app.models.venta import Pago
from app.repositories import pago_repo
from app.schemas.pago_schema import ValidarPagoRequest


_VALID_TARGETS: set[str] = {"aprobado", "rechazado"}


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def validar_pago(
    db: AsyncSession,
    id_pago: int,
    data: ValidarPagoRequest,
    id_usuario_validacion: int,
) -> Pago:
    """Approve or reject a pending payment.

    Validations:
    1. Payment must exist.
    2. Payment must be in 'pendiente' state.
    3. Payment method must require comprobante (e.g. transferencia).
    4. Target state must be 'aprobado' or 'rechazado' (not 'pendiente').
    """
    # 1. Payment must exist
    pago = await pago_repo.get_by_id(db, id_pago)
    if not pago:
        raise MajesaError(f"Pago {id_pago} no encontrado", 404)

    # 2. Must be pending
    if pago.estado_validacion != "pendiente":
        raise MajesaError(
            f"El pago ya fue validado (estado actual: {pago.estado_validacion!r})",
            409,
        )

    # 3. Payment method must require comprobante
    if not pago.metodo_pago.requiere_comprobante:
        raise MajesaError(
            "Este método de pago no requiere validación de comprobante",
            422,
        )

    # 4. Target state validation
    target = data.estado_validacion.value
    if target not in _VALID_TARGETS:
        raise MajesaError(
            "El estado de validación debe ser 'aprobado' o 'rechazado'",
            422,
        )

    # All validations passed — update
    pago = await pago_repo.update(
        db,
        pago,
        {
            "estado_validacion": target,
            "id_usuario_validacion": id_usuario_validacion,
            "fecha_validacion": _now(),
        },
    )
    await db.commit()
    return pago