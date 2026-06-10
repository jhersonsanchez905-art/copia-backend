"""
auditoria_schema.py
Pydantic schemas for Auditoria (read-only; generated automatically by middleware).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class AccionEnum(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class EstadoAuditoriaEnum(str, Enum):
    exitoso = "exitoso"
    fallido = "fallido"


class AuditoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_auditoria: int
    id_usuario: Optional[int] = None
    entidad: str
    id_registro: Optional[int] = None
    accion: AccionEnum
    estado: EstadoAuditoriaEnum
    descripcion: Optional[str] = None
    payload: Optional[Any] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    fecha: datetime
