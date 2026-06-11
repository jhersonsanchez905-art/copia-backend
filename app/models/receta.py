"""
receta.py
Modelos de recetas versionadas del sistema POS.
Autor: SebastianValero12
Issue: #20 — actualizado para separar RecetaDetalleInsumo y RecetaDetalleSubreceta
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class RecetaVersion(Base):
    __tablename__ = "receta_version"
    __table_args__ = {"schema": "pos"}

    id_receta_version = Column(Integer, primary_key=True, index=True)
    id_producto = Column(Integer, ForeignKey("pos.producto.id_producto"), nullable=False)
    version = Column(Integer, nullable=False)
    vigente = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), default=_now)
    costo_total = Column(Numeric(14, 4))
    tiempo_preparacion_min = Column(Integer)
    instrucciones_generales = Column(String)
    observaciones = Column(String)

    producto = relationship("Producto", back_populates="recetas")
    detalles_insumo = relationship("RecetaDetalleInsumo", back_populates="receta_version", cascade="all, delete-orphan")
    detalles_subreceta = relationship("RecetaDetalleSubreceta", back_populates="receta_version", cascade="all, delete-orphan")
    pasos = relationship("RecetaPaso", back_populates="receta_version", cascade="all, delete-orphan")
    item_ventas = relationship("ItemVenta", back_populates="receta_version")

    @property
    def nombre_producto(self) -> str | None:
        return self.producto.nombre if self.producto else None


class RecetaDetalleInsumo(Base):
    """Línea de insumo directo dentro de una versión de receta."""

    __tablename__ = "receta_detalle_insumo"
    __table_args__ = {"schema": "pos"}

    id_receta_detalle_insumo = Column(Integer, primary_key=True, index=True)
    id_receta_version = Column(Integer, ForeignKey("pos.receta_version.id_receta_version"), nullable=False)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    costo_unitario = Column(Numeric(14, 4))
    costo_total = Column(Numeric(14, 4))
    pct_participacion = Column(Numeric(5, 2))

    receta_version = relationship("RecetaVersion", back_populates="detalles_insumo")
    insumo = relationship("Insumo", back_populates="receta_detalles")
    unidad = relationship("UnidadMedida")


class RecetaDetalleSubreceta(Base):
    """Línea de subreceta dentro de una versión de receta."""

    __tablename__ = "receta_detalle_subreceta"
    __table_args__ = {"schema": "pos"}

    id_receta_detalle_subreceta = Column(Integer, primary_key=True, index=True)
    id_receta_version = Column(Integer, ForeignKey("pos.receta_version.id_receta_version"), nullable=False)
    id_subreceta = Column(Integer, ForeignKey("pos.subreceta.id_subreceta"), nullable=False)
    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    costo_unitario = Column(Numeric(14, 4))
    costo_total = Column(Numeric(14, 4))
    pct_participacion = Column(Numeric(5, 2))

    receta_version = relationship("RecetaVersion", back_populates="detalles_subreceta")
    subreceta = relationship("Subreceta", back_populates="receta_detalles")
    unidad = relationship("UnidadMedida")


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