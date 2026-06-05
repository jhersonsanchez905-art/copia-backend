"""
inventario.py

Inventory models for the POS system: inventory movements and stock alerts.

Author: Suley Suarez
Issue: #21
"""

import datetime
 
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
 
from app.database import Base
 
 
def _now():
    return datetime.datetime.now(datetime.timezone.utc)
 
 
class MovimientoInventario(Base):
    """
    Registro automático de cada entrada, salida o merma de inventario.
    No tiene flujo de aprobación — eso es AjusteInventario.
    Se genera automáticamente al registrar una venta o recibir una orden de compra.
    """
 
    __tablename__ = "movimiento_inventario"
    __table_args__ = {"schema": "pos"}
 
    id_movimiento = Column(Integer, primary_key=True, index=True)
 
    id_insumo = Column(
        Integer,
        ForeignKey("pos.insumo.id_insumo"),
        nullable=False,  # todo movimiento afecta un insumo específico
    )
 
    # entrada | salida | merma
    tipo = Column(String(20), nullable=False)
 
    cantidad = Column(Numeric(12, 4), nullable=False)
    cantidad_anterior = Column(Numeric(12, 4), nullable=False)
    cantidad_nueva = Column(Numeric(12, 4), nullable=False)
 
    motivo = Column(String)
    observacion = Column(String)
 
    # origen del movimiento — solo uno de estos estará poblado
    id_venta = Column(
        Integer,
        ForeignKey("pos.venta.id_venta"),
        nullable=True,
    )
    id_orden_compra = Column(
        Integer,
        ForeignKey("pos.orden_compra.id_orden_compra"),
        nullable=True,
    )
 
    id_usuario = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=False,
    )
 
    fecha = Column(DateTime(timezone=True), default=_now, nullable=False)
 
    # --- relaciones ---
    insumo = relationship("Insumo", back_populates="movimientos")
    venta = relationship("Venta")
    orden_compra = relationship("OrdenCompra")
    usuario = relationship("Usuario")
 
 
class Alerta(Base):
    """
    Alerta de stock por cantidad (semáforo rojo/amarillo).
    Distinta a AlertaPerecible que es por tiempo de permanencia.
    """
 
    __tablename__ = "alerta"
    __table_args__ = {"schema": "pos"}
 
    id_alerta = Column(Integer, primary_key=True, index=True)
 
    id_insumo = Column(
        Integer,
        ForeignKey("pos.insumo.id_insumo"),
        nullable=False,
    )
 
    # stock_bajo | stock_critico
    tipo = Column(String(20), nullable=False, default="stock_bajo")
 
    # activa | resuelta
    estado = Column(String(20), nullable=False, default="activa")
 
    # verde | amarillo | rojo
    semaforo = Column(String(10), nullable=False)
 
    cantidad_a_pedir = Column(Numeric(12, 4))
 
    id_orden_compra = Column(
        Integer,
        ForeignKey("pos.orden_compra.id_orden_compra"),
        nullable=True,
    )
 
    fecha_creacion = Column(DateTime(timezone=True), default=_now, nullable=False)
    fecha_resolucion = Column(DateTime(timezone=True), nullable=True)
 
    # --- relaciones ---
    insumo = relationship("Insumo", back_populates="alertas")
    orden_compra = relationship("OrdenCompra")