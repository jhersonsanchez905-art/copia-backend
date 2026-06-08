"""
stock.py
Stock actual por insumo. Separado del catálogo para cumplir 3FN.
Issue: nuevo
"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = {"schema": "pos"}

    id_stock = Column(Integer, primary_key=True, index=True)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False, unique=True)
    cantidad = Column(Numeric(12, 4), nullable=False, default=0)
    # verde | amarillo | rojo
    semaforo = Column(String(10), nullable=False, default="verde")
    ultima_actualizacion = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    insumo = relationship("Insumo", back_populates="stock")
    alertas_perecibles = relationship("AlertaPerecible", back_populates="stock")
