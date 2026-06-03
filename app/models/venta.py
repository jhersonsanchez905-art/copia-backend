"""
venta.py

Sales models for the POS system: sales, sale items, payments,
invoices and returns.

Autor: Suley Suarez
Issue: #21
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    JSON,
)

from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Venta(Base):
    __tablename__ = "venta"
    __table_args__ = {"schema": "pos"}

    id_venta = Column(Integer, primary_key=True, index=True)

    fecha = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )

    id_usuario = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=False,
    )

    id_cliente = Column(
        Integer,
        ForeignKey("pos.cliente.id_cliente"),
        nullable=True,
    )

    subtotal = Column(
        Numeric(16, 2),
        nullable=False,
        default=0,
    )

    total = Column(
        Numeric(16, 2),
        nullable=False,
        default=0,
    )

    estado = Column(
        String,
        nullable=False,
        default="COMPLETADA",
    )

    usuario = relationship(
        "Usuario",
        back_populates="ventas",
    )

    cliente = relationship(
        "Cliente",
        back_populates="ventas",
    )

    items = relationship(
        "ItemVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
    )

    pagos = relationship(
        "Pago",
        back_populates="venta",
        cascade="all, delete-orphan",
    )

    factura = relationship(
        "Factura",
        back_populates="venta",
        uselist=False,
    )


class ItemVenta(Base):
    __tablename__ = "item_venta"
    __table_args__ = {"schema": "pos"}

    id_item_venta = Column(Integer, primary_key=True, index=True)

    id_venta = Column(
        Integer,
        ForeignKey("pos.venta.id_venta"),
        nullable=False,
    )

    id_producto = Column(
        Integer,
        ForeignKey("pos.producto.id_producto"),
        nullable=False,
    )

    id_receta_version = Column(
        Integer,
        ForeignKey("pos.receta_version.id_receta_version"),
        nullable=False,
    )

    receta_snapshot = Column(
        JSON,
        nullable=True,
    )

    cantidad = Column(
        Integer,
        nullable=False,
    )

    precio_unitario = Column(
        Numeric(16, 2),
        nullable=False,
    )

    subtotal = Column(
        Numeric(16, 2),
        nullable=False,
    )

    venta = relationship(
        "Venta",
        back_populates="items",
    )

    producto = relationship(
        "Producto",
    )

    receta_version = relationship(
        "RecetaVersion",
    )

    devoluciones = relationship(
        "Devolucion",
        back_populates="item_venta",
    )


class Pago(Base):
    __tablename__ = "pago"
    __table_args__ = {"schema": "pos"}

    id_pago = Column(Integer, primary_key=True, index=True)

    id_venta = Column(
        Integer,
        ForeignKey("pos.venta.id_venta"),
        nullable=False,
    )

    id_metodo_pago = Column(
        Integer,
        ForeignKey("pos.metodo_pago.id_metodo_pago"),
        nullable=False,
    )

    monto = Column(
        Numeric(16, 2),
        nullable=False,
    )

    url_comprobante = Column(
        String,
        nullable=True,
    )

    estado_validacion = Column(
        String,
        default="PENDIENTE",
    )

    venta = relationship(
        "Venta",
        back_populates="pagos",
    )

    metodo_pago = relationship(
        "MetodoPago",
    )


class Factura(Base):
    __tablename__ = "factura"
    __table_args__ = {"schema": "pos"}

    id_factura = Column(Integer, primary_key=True, index=True)

    id_venta = Column(
        Integer,
        ForeignKey("pos.venta.id_venta"),
        nullable=False,
        unique=True,
    )

    numero = Column(
        String,
        nullable=False,
        unique=True,
    )

    fecha_emision = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    total = Column(
        Numeric(16, 2),
        nullable=False,
    )

    url_pdf = Column(
        String,
        nullable=True,
    )

    venta = relationship(
        "Venta",
        back_populates="factura",
    )


class Devolucion(Base):
    __tablename__ = "devolucion"
    __table_args__ = {"schema": "pos"}

    id_devolucion = Column(Integer, primary_key=True, index=True)

    id_item_venta = Column(
        Integer,
        ForeignKey("pos.item_venta.id_item_venta"),
        nullable=False,
    )

    cantidad = Column(
        Integer,
        nullable=False,
    )

    motivo = Column(
        String,
        nullable=False,
    )

    observacion = Column(
        String,
        nullable=True,
    )

    fecha = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    item_venta = relationship(
        "ItemVenta",
        back_populates="devoluciones",
    )