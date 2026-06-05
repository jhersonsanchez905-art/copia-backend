"""
app/models/auditoria.py
Audit log model for traceability of all system actions.
Author: Suley Suarez
"""
import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = {"schema": "pos"}

    id_auditoria = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=True)
    entidad = Column(String(60), nullable=False)
    id_registro = Column(Integer, nullable=True)
    # CREATE | UPDATE | DELETE | LOGIN | LOGOUT | APPROVE | REJECT
    accion = Column(String(20), nullable=False)
    # exitoso | fallido
    estado = Column(String(20), nullable=False, default="exitoso")
    descripcion = Column(String)
    payload = Column(JSON, nullable=True)
    ip = Column(String(45))
    user_agent = Column(String(255))
    fecha = Column(DateTime(timezone=True), default=_now, nullable=False)

    usuario = relationship("Usuario")
