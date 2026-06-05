"""
alerta_perecible.py
Alertas por tiempo de permanencia de insumos en inventario.
Distinta a Alerta de stock (que es por cantidad).
Issue: nuevo
"""

import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class AlertaPerecible(Base):
    __tablename__ = "alerta_perecible"
    __table_args__ = {"schema": "pos"}

    id_alerta_perecible = Column(Integer, primary_key=True, index=True)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    id_stock = Column(Integer, ForeignKey("pos.stock.id_stock"), nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    dias_en_inventario = Column(Integer, nullable=False)
    # activa | resuelta
    estado = Column(String(20), nullable=False, default="activa")
    accion_sugerida = Column(String)
    fecha_creacion = Column(DateTime(timezone=True), default=_now)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)

    insumo = relationship("Insumo", back_populates="alertas_perecibles")
    stock = relationship("Stock", back_populates="alertas_perecibles")
