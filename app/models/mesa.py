"""
mesa.py
Modelos de mesas y reservas del sistema POS.
Issue: nuevo
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Mesa(Base):
    __tablename__ = "mesa"
    __table_args__ = {"schema": "pos"}

    id_mesa = Column(Integer, primary_key=True, index=True)
    numero = Column(String(10), nullable=False, unique=True)
    capacidad = Column(Integer, nullable=False)
    zona = Column(String(60))
    # disponible | ocupada | reservada
    estado = Column(String(20), nullable=False, default="disponible")
    activo = Column(Boolean, nullable=False, default=True)

    reservas = relationship("Reserva", back_populates="mesa")
    pedidos = relationship("Pedido", back_populates="mesa")


class Reserva(Base):
    __tablename__ = "reserva"
    __table_args__ = {"schema": "pos"}

    id_reserva = Column(Integer, primary_key=True, index=True)
    id_mesa = Column(Integer, ForeignKey("pos.mesa.id_mesa"), nullable=False)
    id_cliente = Column(Integer, ForeignKey("pos.cliente.id_cliente"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), nullable=False)
    num_personas = Column(Integer, nullable=False)
    # pendiente | confirmada | cancelada | completada
    estado = Column(String(20), nullable=False, default="pendiente")
    observaciones = Column(String)
    fecha_creacion = Column(DateTime(timezone=True), default=_now)

    mesa = relationship("Mesa", back_populates="reservas")
    cliente = relationship("Cliente", back_populates="reservas")
    usuario = relationship("Usuario", back_populates="reservas")
    pedido = relationship("Pedido", back_populates="reserva", uselist=False)
