"""
orden_compra.py
Modelos de órdenes de compra de insumos: cabecera de orden y líneas de detalle por insumo.
Autor: Ivan Ospino
Issue: #19
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, Date, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import enum


class EstadoOrdenCompra(str, enum.Enum):
    BORRADOR = "BORRADOR"
    ENVIADA = "ENVIADA"
    RECIBIDA_PARCIAL = "RECIBIDA_PARCIAL"
    RECIBIDA_TOTAL = "RECIBIDA_TOTAL"
    CANCELADA = "CANCELADA"


class OrdenCompra(Base):
    __tablename__ = "orden_compra"
    __table_args__ = {"schema": "pos"}

    id_orden_compra = Column(Integer, primary_key=True, index=True)
    id_proveedor = Column(Integer, ForeignKey("pos.proveedor.id_proveedor"))
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"))
    numero_orden = Column(String, nullable=False, unique=True, index=True)
    fecha_emision = Column(Date, default=datetime.date.today)
    fecha_entrega_esperada = Column(Date)
    fecha_recepcion_real = Column(Date)
    estado = Column(Enum(EstadoOrdenCompra), default=EstadoOrdenCompra.BORRADOR)
    subtotal = Column(Numeric(16, 2), default=0)
    impuestos = Column(Numeric(16, 2), default=0)
    total = Column(Numeric(16, 2), default=0)
    notas = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    proveedor = relationship("Proveedor", back_populates="ordenes_compra")
    usuario = relationship("Usuario", back_populates="ordenes_compra")
    detalles = relationship("OrdenCompraDetalle", back_populates="orden_compra")


class OrdenCompraDetalle(Base):
    __tablename__ = "orden_compra_detalle"
    __table_args__ = {"schema": "pos"}

    id_detalle = Column(Integer, primary_key=True, index=True)
    id_orden_compra = Column(Integer, ForeignKey("pos.orden_compra.id_orden_compra"), nullable=False)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    cantidad_solicitada = Column(Numeric(12, 4), nullable=False)
    cantidad_recibida = Column(Numeric(12, 4), default=0)
    precio_unitario = Column(Numeric(14, 4), default=0)
    subtotal_linea = Column(Numeric(16, 2), default=0)
    notas = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    orden_compra = relationship("OrdenCompra", back_populates="detalles")
    insumo = relationship("Insumo")