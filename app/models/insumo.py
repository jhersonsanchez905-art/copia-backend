"""
insumo.py
Modelos de insumos y subrecetas del sistema POS.
Autor: Ivan Ospino
Issue: #19
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

from sqlalchemy.orm import relationship
from app.database import Base
import datetime


# =========================
# INSUMO
# =========================
class Insumo(Base):
    __tablename__ = "insumo"
    __table_args__ = {"schema": "pos"}

    id_insumo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True)
    presentacion = Column(String)

    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    id_clasificacion = Column(Integer, ForeignKey("pos.clasificacion.id_clasificacion"), nullable=False)
    id_proveedor = Column(Integer, ForeignKey("pos.proveedor.id_proveedor"), nullable=False)
    id_marca = Column(Integer, ForeignKey("pos.marca.id_marca"), nullable=True)

    contador_unidades = Column(Integer)
    precio = Column(Numeric(14, 4))
    pct_rendimiento = Column(Numeric(5, 2))
    precio_real = Column(Numeric(14, 4))
    precio_por_udm = Column(Numeric(14, 4))

    stock_actual = Column(Numeric(12, 4), default=0)
    umbral_minimo = Column(Numeric(12, 4), default=0)

    activo = Column(Boolean, default=True)

    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    unidad = relationship("UnidadMedida", back_populates="insumos")
    clasificacion = relationship("Clasificacion", back_populates="insumos")
    proveedor = relationship("Proveedor", back_populates="insumos")
    marca = relationship("Marca", back_populates="insumos")

    receta_detalles = relationship("RecetaDetalle", back_populates="insumo")
    subreceta_ingredientes = relationship("SubrecetaIngrediente", back_populates="insumo")
    movimientos = relationship("MovimientoInventario", back_populates="insumo")
    alertas = relationship("Alerta", back_populates="insumo")


# =========================
# SUBRECETA
# =========================
class Subreceta(Base):
    __tablename__ = "subreceta"
    __table_args__ = {"schema": "pos"}

    id_subreceta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    porciones = Column(Integer)
    peso_porcion_gr = Column(Numeric(12, 4))
    costo_total = Column(Numeric(14, 4))
    stock_actual = Column(Numeric(12, 4), default=0)
    activo = Column(Boolean, default=True)

    ingredientes = relationship("SubrecetaIngrediente", back_populates="subreceta")


# =========================
# SUBRECETA INGREDIENTE
# =========================
class SubrecetaIngrediente(Base):
    __tablename__ = "subreceta_ingrediente"
    __table_args__ = {"schema": "pos"}

    id_subreceta_ing = Column(Integer, primary_key=True, index=True)

    id_subreceta = Column(Integer, ForeignKey("pos.subreceta.id_subreceta"))
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"))

    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"))

    cantidad = Column(Numeric(14, 4))
    costo_unitario = Column(Numeric(14, 4))
    costo_total = Column(Numeric(14, 4))
    pct_participacion = Column(Numeric(5, 2))

    subreceta = relationship("Subreceta", back_populates="ingredientes")
    insumo = relationship("Insumo", back_populates="subreceta_ingredientes")