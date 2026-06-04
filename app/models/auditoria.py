"""
app/models/auditoria.py

Audit log model for traceability of all system actions.

Author: Suley Suarez
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = {"schema": "pos"}

    id_auditoria = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=True)
    action_performed = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    descripcion = Column(String(255))
    payload = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True)
    tms = Column(DateTime, default=datetime.utcnow, nullable=False)