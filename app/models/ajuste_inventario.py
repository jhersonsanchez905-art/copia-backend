"""
ajuste_inventario.py
Ajustes manuales de inventario con flujo de aprobación.
Issue: nuevo
"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class AjusteInventario(Base):
    __tablename__ = "ajuste_inventario"
    __table_args__ = {"schema": "pos"}

    id_ajuste = Column(Integer, primary_key=True, index=True)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    id_usuario_solicita = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    id_usuario_aprueba = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=True)
    cantidad = Column(Numeric(12, 4), nullable=False)
    motivo = Column(String, nullable=False)
    observacion = Column(String)
    # pendiente | aprobado | rechazado
    estado = Column(String(20), nullable=False, default="pendiente")
    fecha_solicitud = Column(DateTime(timezone=True), default=_now)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)

    insumo = relationship("Insumo", back_populates="ajustes")
    usuario_solicita = relationship("Usuario", foreign_keys=[id_usuario_solicita])
    usuario_aprueba = relationship("Usuario", foreign_keys=[id_usuario_aprueba])
