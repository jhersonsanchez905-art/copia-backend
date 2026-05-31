"""
campanas.py
Modelos de campañas de marketing del sistema.
Autor: charlykj
Issue: #18
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class TipoCampana(Base):
    __tablename__ = "tipo_campana"
    __table_args__ = {"schema": "mkt"}

    id_tipo_campana = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)

    campanas = relationship("Campana", back_populates="tipo_campana")


class Canal(Base):
    __tablename__ = "canal"
    __table_args__ = {"schema": "mkt"}

    id_canal = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)


class Campana(Base):
    __tablename__ = "campana"
    __table_args__ = {"schema": "mkt"}

    id_campana = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    id_tipo_campana = Column(Integer, ForeignKey("mkt.tipo_campana.id_tipo_campana"))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    baseline_dias = Column(Integer)
    presupuesto = Column(Numeric)
    estado = Column(String)
    id_usuario = Column(Integer, ForeignKey("pos.usuario.id_usuario"))
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    tipo_campana = relationship("TipoCampana", back_populates="campanas")
    canales = relationship("CampanaCanal", back_populates="campana")
    productos = relationship("CampanaProducto", back_populates="campana")


class CampanaCanal(Base):
    __tablename__ = "campana_canal"
    __table_args__ = {"schema": "mkt"}

    id_campana = Column(Integer, ForeignKey("mkt.campana.id_campana"), primary_key=True)
    id_canal = Column(Integer, ForeignKey("mkt.canal.id_canal"), primary_key=True)

    campana = relationship("Campana", back_populates="canales")


class CampanaProducto(Base):
    __tablename__ = "campana_producto"
    __table_args__ = {"schema": "mkt"}

    id_campana_producto = Column(Integer, primary_key=True, index=True)
    id_campana = Column(Integer, ForeignKey("mkt.campana.id_campana"))
    id_producto = Column(Integer, ForeignKey("pos.producto.id_producto"))
    descuento_pct = Column(Numeric)

    campana = relationship("Campana", back_populates="productos")