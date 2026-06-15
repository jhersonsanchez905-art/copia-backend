"""ETL audit trail helpers for the BI module.

Provides the Step enum (mirrors bi.etl_step seed values), the async
context manager `paso()` for per-step audit logging, and the
execution lifecycle functions (iniciar_ejecucion, cerrar_ejecucion,
registrar_fallo) backed by bi.etl_ejecucion / bi.audit_etl.

Author: Jherson Sanchez
Issue: BI-001

╔══════════════════════════════════════════════════════════════╗
║  MÓDULO BI — SOLO EQUIPO BI DEBE MODIFICAR ESTE ARCHIVO     ║
║  BI MODULE — ONLY THE BI TEAM SHOULD MODIFY THIS FILE       ║
╚══════════════════════════════════════════════════════════════╝
"""

from datetime import date
from enum import IntEnum

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class Step(IntEnum):
    """Mirrors the seed values of bi.etl_step (DDL v3, §3.1)."""

    EJECUCION = 0
    LECTURA_FUENTES = 1
    KPI_PRODUCTO = 2
    KPI_HORAS = 3
    KPI_INSUMO = 4
    KPI_CONSUMO = 5
    RESUMENES_DIARIOS = 6
    RESUMENES_MENSUALES = 7
    WEBHOOK_FRONT = 8
    CORREO_SOPORTE = 9


class Status(IntEnum):
    """Mirrors the seed values of bi.etl_status (DDL v3, §3.1)."""

    INICIADO = 1
    EXITOSO = 2
    FALLIDO_REINTENTABLE = 3
    FALLIDO_DEFINITIVO = 4
    OMITIDO = 5


async def iniciar_ejecucion(db: AsyncSession, fecha: date, origen: str) -> int:
    """Create a new bi.etl_ejecucion row and its initial audit event.

    Args:
        db: Async database session (transaction managed by caller).
        fecha: Business day being processed (fecha_procesada).
        origen: One of 'cron', 'retrigger', 'manual'.

    Returns:
        The id_ejecucion of the newly created row.
    """
    result = await db.execute(
        text("""
            INSERT INTO bi.etl_ejecucion
                (fecha_procesada, origen, intento, id_status)
            VALUES (:fecha, :origen, 1, :status_iniciado)
            RETURNING id_ejecucion
        """),
        {
            "fecha": fecha,
            "origen": origen,
            "status_iniciado": Status.INICIADO,
        },
    )
    id_ejecucion = result.scalar_one()

    await db.execute(
        text("""
            INSERT INTO bi.audit_etl
                (id_ejecucion, id_step, id_status, descripcion)
            VALUES (:id_ejecucion, :step, :status, :descripcion)
        """),
        {
            "id_ejecucion": id_ejecucion,
            "step": Step.EJECUCION,
            "status": Status.INICIADO,
            "descripcion": f"ETL iniciado (origen={origen})",
        },
    )
    return id_ejecucion
