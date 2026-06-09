"""
pedido.py
Modelos de pedidos del sistema POS.
Issue: nuevo
"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Pedido(Base):
    __tablename__ = "pedido"
    __table_args__ = {"schema": "pos"}

    id_pedido = Column(Integer, primary_key=True, index=True)
    id_mesa = Column(Integer, ForeignKey("pos.mesa.id_mesa"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    id_reserva = Column(Integer, ForeignKey("pos.reserva.id_reserva"), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), default=_now)
    # abierto | enviado | pagado | cancelado
    estado = Column(String(20), nullable=False, default="abierto")
    observaciones = Column(String)

    mesa = relationship("Mesa", back_populates="pedidos")
    usuario = relationship("Usuario", back_populates="pedidos")
    reserva = relationship("Reserva", back_populates="pedido")
    items = relationship("PedidoItem", back_populates="pedido", cascade="all, delete-orphan")
    servicios = relationship("PedidoServicio", back_populates="pedido", cascade="all, delete-orphan")
    venta = relationship("Venta", back_populates="pedido", uselist=False)


class PedidoItem(Base):
    __tablename__ = "pedido_item"
    __table_args__ = {"schema": "pos"}

    id_pedido_item = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pos.pedido.id_pedido"), nullable=False)
    id_producto = Column(Integer, ForeignKey("pos.producto.id_producto"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(14, 2), nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=False)
    observaciones = Column(String)
    # pendiente | en_preparacion | listo | entregado | cancelado
    estado = Column(String(20), nullable=False, default="pendiente")

    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="pedido_items")


class PedidoServicio(Base):
    __tablename__ = "pedido_servicio"
    __table_args__ = {"schema": "pos"}

    id_pedido_servicio = Column(Integer, primary_key=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pos.pedido.id_pedido"), nullable=False)
    id_servicio = Column(Integer, ForeignKey("pos.servicio_adicional.id_servicio"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    valor_unitario = Column(Numeric(14, 2), nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=False)
    observaciones = Column(String)

    pedido = relationship("Pedido", back_populates="servicios")
    servicio = relationship("ServicioAdicional")
