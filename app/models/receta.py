"""
receta.py
Modelos de recetas versionadas del sistema POS: versiones, detalles de
ingredientes y pasos de preparación.
Autor: SebastianValero12
Issue: #20
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class RecetaVersion(Base):
    __tablename__ = "receta_version"
    __table_args__ = {"schema": "pos"}

    id_receta_version = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer, ForeignKey("pos.producto.id_producto"), nullable=False)
    version = Column(Integer, nullable=False)
    vigente = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    costo_total = Column(Numeric)
    tiempo_preparacion_min = Column(Integer)
    instrucciones_generales = Column(String)
    observaciones = Column(String)

    producto = relationship("Producto", back_populates="recetas")
    detalles = relationship("RecetaDetalle", back_populates="receta_version")
    pasos = relationship("RecetaPaso", back_populates="receta_version")


class RecetaDetalle(Base):
    __tablename__ = "receta_detalle"
    __table_args__ = {"schema": "pos"}

    id_receta_detalle = Column(Integer, primary_key=True, index=True)
    id_receta_version = Column(Integer, ForeignKey("pos.receta_version.id_receta_version"), nullable=False)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=True)
    id_subreceta = Column(Integer, ForeignKey("pos.subreceta.id_subreceta"), nullable=True)
    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    cantidad = Column(Numeric, nullable=False)
    costo_unitario = Column(Numeric)
    costo_total = Column(Numeric)
    pct_participacion = Column(Numeric)

    receta_version = relationship("RecetaVersion", back_populates="detalles")


class RecetaPaso(Base):
    __tablename__ = "receta_paso"
    __table_args__ = {"schema": "pos"}

    id_paso = Column(Integer, primary_key=True, index=True)
    id_receta_version = Column(Integer, ForeignKey("pos.receta_version.id_receta_version"), nullable=False)
    numero_paso = Column(Integer, nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    tiempo_estimado_min = Column(Integer)

    receta_version = relationship("RecetaVersion", back_populates="pasos")