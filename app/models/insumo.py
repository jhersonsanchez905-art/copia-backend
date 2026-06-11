"""
insumo.py
Modelos de insumos y subrecetas del sistema POS.
Autor: Ivan Ospino
Issue: #19
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


class Insumo(Base):
    __tablename__ = "insumo"
    __table_args__ = {"schema": "pos"}

    id_insumo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, unique=True)
    presentacion = Column(String(120))

    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    id_clasificacion = Column(Integer, ForeignKey("pos.clasificacion.id_clasificacion"), nullable=False)
    # nullable=True: proveedor principal va en InsumoProveedor, no fijo aquí
    id_marca = Column(Integer, ForeignKey("pos.marca.id_marca"), nullable=True)

    contador_unidades = Column(Integer)
    precio = Column(Numeric(14, 4))
    pct_rendimiento = Column(Numeric(5, 2))
    # precio_real y precio_por_udm son calculados, no se persisten
    umbral_minimo = Column(Numeric(12, 4), nullable=False, default=0)
    stock_minimo = Column(Numeric(12, 4), nullable=False, default=0)
    stock_maximo = Column(Numeric(12, 4), nullable=True)
    punto_pedido = Column(Numeric(12, 4), nullable=True)
    cantidad_a_pedir = Column(Numeric(12, 4), nullable=True)
    dias_anticipacion = Column(Integer, nullable=True)

    activo = Column(Boolean, nullable=False, default=True)

    fecha_creacion = Column(DateTime(timezone=True), nullable=False, default=_now)
    fecha_actualizacion = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    # --- propiedades calculadas ---
    @property
    def precio_real(self):
        if self.precio is None or self.pct_rendimiento is None:
            return None
        from decimal import Decimal
        return self.precio / (self.pct_rendimiento / Decimal("100"))

    @property
    def precio_por_udm(self):
        if self.precio is None or not self.contador_unidades:
            return None
        from decimal import Decimal
        return self.precio / Decimal(self.contador_unidades)

    # --- relaciones ---
    unidad = relationship("UnidadMedida", back_populates="insumos")
    clasificacion = relationship("Clasificacion", back_populates="insumos")
    marca = relationship("Marca", back_populates="insumos")
    proveedores = relationship("InsumoProveedor", back_populates="insumo")

    stock = relationship("Stock", back_populates="insumo", uselist=False)
    movimientos = relationship("MovimientoInventario", back_populates="insumo")
    ajustes = relationship("AjusteInventario", back_populates="insumo")
    alertas = relationship("Alerta", back_populates="insumo")
    alertas_perecibles = relationship("AlertaPerecible", back_populates="insumo")

    subreceta_ingredientes = relationship("SubrecetaIngrediente", back_populates="insumo")
    receta_detalles = relationship("RecetaDetalleInsumo", back_populates="insumo")
    orden_compra_detalles = relationship("OrdenCompraDetalle", back_populates="insumo")

    def __repr__(self):
        return f"<Insumo id={self.id_insumo} nombre={self.nombre!r}>"


class Subreceta(Base):
    __tablename__ = "subreceta"
    __table_args__ = {"schema": "pos"}

    id_subreceta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False, unique=True)
    porciones = Column(Integer)
    peso_porcion_gr = Column(Numeric(12, 4))
    costo_total = Column(Numeric(14, 4))
    # stock_actual eliminado — subrecetas no tienen stock propio,
    # sus insumos se descuentan directamente
    activo = Column(Boolean, nullable=False, default=True)

    ingredientes = relationship("SubrecetaIngrediente", back_populates="subreceta", cascade="all, delete-orphan")
    receta_detalles = relationship("RecetaDetalleSubreceta", back_populates="subreceta")

    def __repr__(self):
        return f"<Subreceta id={self.id_subreceta} nombre={self.nombre!r}>"


class SubrecetaIngrediente(Base):
    __tablename__ = "subreceta_ingrediente"
    __table_args__ = {"schema": "pos"}

    id_subreceta_ing = Column(Integer, primary_key=True, index=True)
    id_subreceta = Column(Integer, ForeignKey("pos.subreceta.id_subreceta"), nullable=False)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    id_unidad = Column(Integer, ForeignKey("pos.unidad_medida.id_unidad"), nullable=False)
    cantidad = Column(Numeric(12, 4), nullable=False)
    costo_unitario = Column(Numeric(14, 4))
    costo_total = Column(Numeric(14, 4))
    pct_participacion = Column(Numeric(5, 2))

    subreceta = relationship("Subreceta", back_populates="ingredientes")
    insumo = relationship("Insumo", back_populates="subreceta_ingredientes")
    unidad = relationship("UnidadMedida")

    def __repr__(self):
        return f"<SubrecetaIngrediente subreceta={self.id_subreceta} insumo={self.id_insumo}>"