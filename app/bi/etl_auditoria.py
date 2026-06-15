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

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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


@asynccontextmanager
async def paso(db: AsyncSession, id_ejecucion: int, step: Step) -> AsyncIterator[dict]:
    """Audit-log a single ETL step.

    Records an 'iniciado' event on enter, and 'exitoso'/'fallido_*' on
    exit, including elapsed time. The caller can write to the returned
    dict's 'filas' key to report rows affected (e.g. from rowcount).

    On exception, logs a 'fallido_reintentable' audit event and
    re-raises — does not swallow errors (rollback is procesar_dia's job).

    Args:
        db: Async database session (transaction managed by caller).
        id_ejecucion: The bi.etl_ejecucion id from iniciar_ejecucion.
        step: Which ETL step is being audited.

    Yields:
        A dict with key 'filas' (int, default 0) for the caller to set.
    """
    inicio = time.monotonic()
    info: dict = {"filas": 0}

    await db.execute(
        text("""
            INSERT INTO bi.audit_etl
                (id_ejecucion, id_step, id_status, descripcion)
            VALUES (:id_ejecucion, :step, :status, NULL)
        """),
        {
            "id_ejecucion": id_ejecucion,
            "step": step,
            "status": Status.INICIADO,
        },
    )

    try:
        yield info
    except Exception as exc:
        duracion_ms = int((time.monotonic() - inicio) * 1000)
        await db.execute(
            text("""
                INSERT INTO bi.audit_etl
                    (id_ejecucion, id_step, id_status,
                     descripcion, duracion_ms)
                VALUES (:id_ejecucion, :step, :status,
                        :descripcion, :duracion_ms)
            """),
            {
                "id_ejecucion": id_ejecucion,
                "step": step,
                "status": Status.FALLIDO_REINTENTABLE,
                "descripcion": str(exc)[:500],
                "duracion_ms": duracion_ms,
            },
        )
        raise
    else:
        duracion_ms = int((time.monotonic() - inicio) * 1000)
        await db.execute(
            text("""
                INSERT INTO bi.audit_etl
                    (id_ejecucion, id_step, id_status,
                     filas_afectadas, duracion_ms)
                VALUES (:id_ejecucion, :step, :status,
                        :filas, :duracion_ms)
            """),
            {
                "id_ejecucion": id_ejecucion,
                "step": step,
                "status": Status.EXITOSO,
                "filas": info["filas"],
                "duracion_ms": duracion_ms,
            },
        )
