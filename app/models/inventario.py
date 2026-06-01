"""
inventario.py

Inventory models for the POS system: inventory movements and stock alerts.

Author: Suley Suarez
Issue: #21
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    DateTime,
    ForeignKey,
)
from app.database import Base
import datetime


class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"
    __table_args__ = {"schema": "pos"}

    id_movimiento = Column(Integer, primary_key=True, index=True)

    id_insumo = Column(
        Integer,
        ForeignKey("pos.insumo.id_insumo"),
        nullable=True,
    )

    id_subreceta = Column(
        Integer,
        ForeignKey("pos.subreceta.id_subreceta"),
        nullable=True,
    )

    tipo = Column(String, nullable=False)

    cantidad = Column(Numeric, nullable=False)

    motivo = Column(String)

    observacion = Column(String)

    afecta_stock = Column(Boolean, default=True)

    cantidad_anterior = Column(Numeric)

    cantidad_nueva = Column(Numeric)

    estado = Column(String)

    id_venta = Column(
        Integer,
        ForeignKey("pos.venta.id_venta"),
        nullable=True,
    )

    id_orden_compra = Column(
        Integer,
        ForeignKey("pos.orden_compra.id_orden"),
        nullable=True,
    )

    id_usuario = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=False,
    )

    id_aprobador = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=True,
    )

    fecha = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )


class Alerta(Base):
    __tablename__ = "alerta"
    __table_args__ = {"schema": "pos"}

    id_alerta = Column(Integer, primary_key=True, index=True)

    id_insumo = Column(
        Integer,
        ForeignKey("pos.insumo.id_insumo"),
        nullable=False,
    )

    estado = Column(String)

    semaforo = Column(String)

    cantidad_a_pedir = Column(Numeric)

    id_orden_compra = Column(
        Integer,
        ForeignKey("pos.orden_compra.id_orden"),
        nullable=True,
    )

    fecha_creacion = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    fecha_resolucion = Column(DateTime)