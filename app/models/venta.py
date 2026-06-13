"""
venta.py
Modelos de ventas del sistema POS: ventas, items, pagos, facturas y devoluciones.
Autor: Suley Suarez
Issue: #21
"""

import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Venta(Base):
    __tablename__ = "venta"
    __table_args__ = {"schema": "pos"}

    id_venta = Column(Integer, primary_key=True, index=True)

    id_apertura = Column(Integer, ForeignKey("pos.apertura_caja.id_apertura"), nullable=False)
    id_pedido = Column(Integer, ForeignKey("pos.pedido.id_pedido"), nullable=True, unique=True)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    id_cliente = Column(Integer, ForeignKey("pos.cliente.id_cliente"), nullable=True)

    turno = Column(String(20), nullable=False)
    fecha = Column(DateTime(timezone=True), default=_now, nullable=False)
    subtotal = Column(Numeric(16, 2), nullable=False, default=0)
    total = Column(Numeric(16, 2), nullable=False, default=0)
    # abierta | completada | anulada
    estado = Column(String(20), nullable=False, default="abierta")
    token_idempotencia = Column(String(64), unique=True, nullable=True, index=True)

    # --- relaciones ---
    apertura = relationship("AperturaCaja", back_populates="ventas")
    pedido = relationship("Pedido", back_populates="venta")
    usuario = relationship("Usuario", back_populates="ventas")
    cliente = relationship("Cliente", back_populates="ventas")
    items = relationship("ItemVenta", back_populates="venta", cascade="all, delete-orphan")
    pagos = relationship("Pago", back_populates="venta", cascade="all, delete-orphan")
    factura = relationship("Factura", back_populates="venta", uselist=False)
    movimientos = relationship("MovimientoInventario", back_populates="venta")
    devoluciones = relationship("Devolucion", back_populates="venta")

    def __repr__(self):
        return f"<Venta id={self.id_venta} estado={self.estado}>"


class ItemVenta(Base):
    __tablename__ = "item_venta"
    __table_args__ = {"schema": "pos"}

    id_item_venta = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("pos.venta.id_venta"), nullable=False)
    id_producto = Column(Integer, ForeignKey("pos.producto.id_producto"), nullable=False)
    id_receta_version = Column(Integer, ForeignKey("pos.receta_version.id_receta_version"), nullable=False)
    receta_snapshot = Column(JSON, nullable=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(16, 2), nullable=False)
    subtotal = Column(Numeric(16, 2), nullable=False)

    venta = relationship("Venta", back_populates="items")
    producto = relationship("Producto", back_populates="item_ventas")
    receta_version = relationship("RecetaVersion", back_populates="item_ventas")
    devoluciones = relationship("Devolucion", back_populates="item_venta")


class Pago(Base):
    __tablename__ = "pago"
    __table_args__ = {"schema": "pos"}

    id_pago = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("pos.venta.id_venta"), nullable=False)
    id_metodo_pago = Column(Integer, ForeignKey("pos.metodo_pago.id_metodo_pago"), nullable=False)
    id_usuario_validacion = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=True)
    monto = Column(Numeric(16, 2), nullable=False)
    url_comprobante = Column(String, nullable=True)
    # pendiente | aprobado | rechazado
    estado_validacion = Column(String(20), nullable=False, default="pendiente")
    fecha_validacion = Column(DateTime(timezone=True), nullable=True)

    venta = relationship("Venta", back_populates="pagos")
    metodo_pago = relationship("MetodoPago", back_populates="pagos")
    usuario_validacion = relationship("Usuario", foreign_keys=[id_usuario_validacion])


class Factura(Base):
    __tablename__ = "factura"
    __table_args__ = {"schema": "pos"}

    id_factura = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("pos.venta.id_venta"), nullable=False, unique=True)
    numero = Column(String, nullable=False, unique=True)
    fecha_emision = Column(DateTime(timezone=True), default=_now)
    total = Column(Numeric(16, 2), nullable=False)
    url_pdf = Column(String, nullable=True)

    venta = relationship("Venta", back_populates="factura")


class Devolucion(Base):
    __tablename__ = "devolucion"
    __table_args__ = {"schema": "pos"}

    id_devolucion = Column(Integer, primary_key=True, index=True)
    id_venta = Column(Integer, ForeignKey("pos.venta.id_venta"), nullable=False)
    id_item_venta = Column(Integer, ForeignKey("pos.item_venta.id_item_venta"), nullable=False)
    id_aprobador = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=True)
    cantidad = Column(Integer, nullable=False)
    motivo = Column(String, nullable=False)
    observacion = Column(String, nullable=True)
    # pendiente | aprobada | rechazada
    estado = Column(String(20), nullable=False, default="pendiente")
    reintegra_stock = Column(Integer, nullable=False, default=True)
    fecha = Column(DateTime(timezone=True), default=_now)

    venta = relationship("Venta", back_populates="devoluciones")
    item_venta = relationship("ItemVenta", back_populates="devoluciones")
    aprobador = relationship("Usuario", foreign_keys=[id_aprobador])