"""
insumo.py
Modelos de insumos y subrecetas del sistema POS: insumos, subrecetas e ingredientes de subreceta.
Autor: Ivan Ospino
Issue: #19
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Insumo(Base):
    __tablename__ = "insumo"
    __table_args__ = {"schema": "pos"}

    id_insumo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    unidad_medida = Column(String, nullable=False)
    stock_actual = Column(Numeric(12, 4), default=0)
    umbral_minimo = Column(Numeric(12, 4), default=0)
    costo_unitario = Column(Numeric(14, 4))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    subreceta_ingredientes = relationship("SubrecetaIngrediente", back_populates="insumo")


class Subreceta(Base):
    __tablename__ = "subreceta"
    __table_args__ = {"schema": "pos"}

    id_subreceta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    rendimiento = Column(Numeric(12, 4), default=1)
    unidad_rendimiento = Column(String, default="porcion")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    ingredientes = relationship("SubrecetaIngrediente", back_populates="subreceta")


class SubrecetaIngrediente(Base):
    __tablename__ = "subreceta_ingrediente"
    __table_args__ = {"schema": "pos"}

    id_subreceta = Column(Integer, ForeignKey("pos.subreceta.id_subreceta"), primary_key=True)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), primary_key=True)
    cantidad = Column(Numeric(12, 4), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    subreceta = relationship("Subreceta", back_populates="ingredientes")
    insumo = relationship("Insumo", back_populates="subreceta_ingredientes")