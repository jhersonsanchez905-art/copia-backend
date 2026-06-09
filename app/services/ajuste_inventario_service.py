"""
ajuste_inventario_service.py
Lógica de negocio para ajustes manuales de inventario con flujo de aprobación.
Autor: Ivan Ospino
Issue: #21
"""
import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import MajesaError, PermisoDenegadoError
from app.models.ajuste_inventario import AjusteInventario
from app.repositories import ajuste_inventario_repo, insumo_repo
from app.schemas.ajuste_inventario_schema import (
    AjusteInventarioAprobar,
    AjusteInventarioRechazar,
    AjusteInventarioCreate,
)
from app.services import inventario_service


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


async def solicitar_ajuste(
    db: AsyncSession,
    data: AjusteInventarioCreate,
    id_usuario_solicita: int,
) -> AjusteInventario:
    insumo = await insumo_repo.get_insumo_by_id(db, data.id_insumo)
    if not insumo:
        raise MajesaError(f"Insumo {data.id_insumo} no encontrado", 404)

    ajuste = AjusteInventario(
        id_insumo=data.id_insumo,
        id_usuario_solicita=id_usuario_solicita,
        cantidad=data.cantidad,
        motivo=data.motivo,
        observacion=data.observacion,
        estado="pendiente",
        fecha_solicitud=_now(),
    )
    ajuste = await ajuste_inventario_repo.create_ajuste(db, ajuste)
    await db.commit()
    return ajuste


async def aprobar_ajuste(
    db: AsyncSession,
    id_ajuste: int,
    data: AjusteInventarioAprobar,
    id_usuario_aprueba: int,
    es_administrador: bool,
) -> AjusteInventario:
    if not es_administrador:
        raise PermisoDenegadoError()

    ajuste = await ajuste_inventario_repo.get_ajuste_by_id(db, id_ajuste)
    if not ajuste:
        raise MajesaError(f"AjusteInventario {id_ajuste} no encontrado", 404)
    if ajuste.estado != "pendiente":
        raise MajesaError(
            f"Solo se pueden aprobar ajustes en estado pendiente. Estado actual: {ajuste.estado!r}",
            400,
        )

    update_data = {
        "estado": "aprobado",
        "id_usuario_aprueba": id_usuario_aprueba,
        "fecha_resolucion": _now(),
    }
    if data.observacion:
        update_data["observacion"] = data.observacion

    ajuste = await ajuste_inventario_repo.update_ajuste(db, ajuste, update_data)

    if ajuste.cantidad >= 0:
        await inventario_service.ingresar_stock(
            db,
            id_insumo=ajuste.id_insumo,
            cantidad=ajuste.cantidad,
            id_usuario=id_usuario_aprueba,
            motivo=f"Ajuste aprobado: {ajuste.motivo}",
        )
    else:
        await inventario_service.descontar_stock(
            db,
            id_insumo=ajuste.id_insumo,
            cantidad=abs(ajuste.cantidad),
            id_usuario=id_usuario_aprueba,
            motivo=f"Ajuste aprobado: {ajuste.motivo}",
        )

    await db.commit()
    return ajuste


async def rechazar_ajuste(
    db: AsyncSession,
    id_ajuste: int,
    data: AjusteInventarioRechazar,
    id_usuario_aprueba: int,
    es_administrador: bool,
) -> AjusteInventario:
    if not es_administrador:
        raise PermisoDenegadoError()

    ajuste = await ajuste_inventario_repo.get_ajuste_by_id(db, id_ajuste)
    if not ajuste:
        raise MajesaError(f"AjusteInventario {id_ajuste} no encontrado", 404)
    if ajuste.estado != "pendiente":
        raise MajesaError(
            f"Solo se pueden rechazar ajustes en estado pendiente. Estado actual: {ajuste.estado!r}",
            400,
        )

    update_data = {
        "estado": "rechazado",
        "id_usuario_aprueba": id_usuario_aprueba,
        "fecha_resolucion": _now(),
    }
    if data.observacion:
        update_data["observacion"] = data.observacion

    ajuste = await ajuste_inventario_repo.update_ajuste(db, ajuste, update_data)
    await db.commit()
    return ajuste


async def get_ajuste_by_id(db: AsyncSession, id_ajuste: int) -> AjusteInventario:
    ajuste = await ajuste_inventario_repo.get_ajuste_by_id(db, id_ajuste)
    if not ajuste:
        raise MajesaError(f"AjusteInventario {id_ajuste} no encontrado", 404)
    return ajuste


async def get_ajustes(
    db: AsyncSession,
    estado: str | None = None,
    id_insumo: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AjusteInventario]:
    return await ajuste_inventario_repo.get_ajustes(
        db, estado=estado, id_insumo=id_insumo, skip=skip, limit=limit
    )