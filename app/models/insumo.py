"""
insumo.py
Modelos de insumos y subrecetas del sistema POS: insumos, subrecetas e ingredientes de subreceta.
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


class Insumo(Base):
    __tablename__ = "insumo"
    __table_args__ = {"schema": "pos"}

    id_insumo = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, nullable=False, unique=True)

    presentacion = Column(String)

    id_unidad = Column(
        Integer,
        ForeignKey("pos.unidad_medida.id_unidad"),
        nullable=False,
    )

    contador_unidades = Column(Integer)

    precio = Column(Numeric(14, 4))

    pct_rendimiento = Column(Numeric(5, 2))

    precio_real = Column(Numeric(14, 4))

    precio_por_udm = Column(Numeric(14, 4))

    id_clasificacion = Column(
        Integer,
        ForeignKey("pos.clasificacion.id_clasificacion"),
        nullable=False,
    )

    id_proveedor = Column(
        Integer,
        ForeignKey("pos.proveedor.id_proveedor"),
        nullable=False,
    )

    id_marca = Column(
        Integer,
        ForeignKey("pos.marca.id_marca"),
        nullable=True,
    )

    stock_actual = Column(
        Numeric(12, 4),
        default=0,
    )

    umbral_minimo = Column(
        Numeric(12, 4),
        default=0,
    )

    activo = Column(
        Boolean,
        default=True,
    )

    fecha_creacion = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )

    fecha_actualizacion = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    unidad = relationship(
        "UnidadMedida",
        back_populates="insumos",
    )

    clasificacion = relationship(
        "Clasificacion",
        back_populates="insumos",
    )

    proveedor = relationship(
        "Proveedor",
        back_populates="insumos",
    )

    marca = relationship(
        "Marca",
        back_populates="insumos",
    )

    subreceta_ingredientes = relationship(
        "SubrecetaIngrediente",
        back_populates="insumo",
    )

    receta_detalles = relationship(
        "RecetaDetalle",
        back_populates="insumo",
    )

    movimientos = relationship(
        "MovimientoInventario",
        back_populates="insumo",
    )

    alertas = relationship(
        "Alerta",
        back_populates="insumo",
    )
