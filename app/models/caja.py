"""
caja.py

Cash register models for the POS system: opening, closing and closing details.

Author: Suley Suarez
Issue: #21
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class AperturaCaja(Base):
    __tablename__ = "apertura_caja"
    __table_args__ = {"schema": "pos"}

    id_apertura = Column(Integer, primary_key=True, index=True)

    id_usuario = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=False,
    )

    turno = Column(String, nullable=False)

    fecha = Column(Date)

    monto_inicial = Column(Numeric, nullable=False)

    hora_apertura = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    observaciones = Column(String)

    ventas = relationship(
        "Venta",
        backref="apertura",
    )

    cierre = relationship(
        "CierreCaja",
        back_populates="apertura",
        uselist=False,
    )


class CierreCaja(Base):
    __tablename__ = "cierre_caja"
    __table_args__ = {"schema": "pos"}

    id_cierre = Column(Integer, primary_key=True, index=True)

    id_apertura = Column(
        Integer,
        ForeignKey("pos.apertura_caja.id_apertura"),
        nullable=False,
        unique=True,
    )

    id_usuario = Column(
        Integer,
        ForeignKey("pos.usuario.id_usuario"),
        nullable=False,
    )

    turno = Column(String)

    fecha = Column(Date)

    total_general = Column(Numeric)

    total_transacciones = Column(Numeric)

    diferencia = Column(Numeric)

    hora_cierre = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    observaciones = Column(String)

    apertura = relationship(
        "AperturaCaja",
        back_populates="cierre",
    )

    detalles = relationship(
        "CierreCajaDetalle",
        back_populates="cierre",
        cascade="all, delete-orphan",
    )


class CierreCajaDetalle(Base):
    __tablename__ = "cierre_caja_detalle"
    __table_args__ = {"schema": "pos"}

    id_detalle = Column(Integer, primary_key=True, index=True)

    id_cierre = Column(
        Integer,
        ForeignKey("pos.cierre_caja.id_cierre"),
        nullable=False,
    )

    id_metodo_pago = Column(
        Integer,
        ForeignKey("pos.metodo_pago.id_metodo_pago"),
        nullable=False,
    )

    total_esperado = Column(Numeric)

    total_contado = Column(Numeric)

    diferencia = Column(Numeric)

    cierre = relationship(
        "CierreCaja",
        back_populates="detalles",
    )