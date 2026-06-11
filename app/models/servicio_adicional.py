"""
servicio_adicional.py
Servicios extras facturables (fotografía, eventos, etc).
Issue: nuevo
"""

from sqlalchemy import Boolean, Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class ServicioAdicional(Base):
    __tablename__ = "servicio_adicional"
    __table_args__ = {"schema": "pos"}

    id_servicio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, unique=True)
    descripcion = Column(String)
    valor = Column(Numeric(14, 2), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    pedido_servicios = relationship("PedidoServicio", back_populates="servicio")
