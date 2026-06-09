"""
orden_compra.py
Modelos de órdenes de compra de insumos: cabecera de orden y líneas de detalle.
Estados: borrador → enviada → recibida
         borrador → cancelada
         enviada  → cancelada
Autor: Ivan Ospino
Issue: #21
"""

import datetime
import enum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class EstadoOrdenCompra(str, enum.Enum):
    borrador  = "borrador"
    enviada   = "enviada"
    recibida  = "recibida"
    cancelada = "cancelada"


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class OrdenCompra(Base):
    __tablename__ = "orden_compra"
    __table_args__ = {"schema": "pos"}

    id_orden_compra          = Column(Integer, primary_key=True, index=True)
    id_proveedor             = Column(Integer, ForeignKey("pos.proveedor.id_proveedor"), nullable=True)
    id_usuario               = Column(Integer, ForeignKey("pos.usuario.id_usuario"),    nullable=True)
    numero_orden             = Column(String,  nullable=False, unique=True, index=True)
    fecha_emision            = Column(Date,    default=datetime.date.today)
    fecha_entrega_esperada   = Column(Date,    nullable=True)
    fecha_recepcion_real     = Column(Date,    nullable=True)
    estado                   = Column(Enum(EstadoOrdenCompra), nullable=False, default=EstadoOrdenCompra.borrador)
    subtotal                 = Column(Numeric(16, 2), default=0)
    impuestos                = Column(Numeric(16, 2), default=0)
    total                    = Column(Numeric(16, 2), default=0)
    notas                    = Column(Text, nullable=True)
    fecha_creacion           = Column(DateTime(timezone=True), default=_now)
    fecha_actualizacion      = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    proveedor = relationship("Proveedor", back_populates="ordenes_compra")
    usuario   = relationship("Usuario",   back_populates="ordenes_compra")
    detalles  = relationship("OrdenCompraDetalle", back_populates="orden_compra", cascade="all, delete-orphan")


class OrdenCompraDetalle(Base):
    __tablename__ = "orden_compra_detalle"
    __table_args__ = {"schema": "pos"}

    id_detalle           = Column(Integer, primary_key=True, index=True)
    id_orden_compra      = Column(Integer, ForeignKey("pos.orden_compra.id_orden_compra"), nullable=False)
    id_insumo            = Column(Integer, ForeignKey("pos.insumo.id_insumo"),             nullable=False)
    cantidad_solicitada  = Column(Numeric(12, 4), nullable=False)
    cantidad_recibida    = Column(Numeric(12, 4), default=0)
    precio_unitario      = Column(Numeric(14, 4), default=0)
    subtotal_linea       = Column(Numeric(16, 2), default=0)
    notas                = Column(Text, nullable=True)
    fecha_creacion       = Column(DateTime(timezone=True), default=_now)
    fecha_actualizacion  = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    orden_compra = relationship("OrdenCompra", back_populates="detalles")
    insumo       = relationship("Insumo")