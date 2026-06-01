"""
producto.py
Modelos de productos del sistema POS.
Autor: SebastianValero12
Issue: #20
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Producto(Base):
    __tablename__ = "producto"
    __table_args__ = {"schema": "pos"}

    id_producto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    id_categoria = Column(Integer, ForeignKey("pos.categoria.id_categoria"))
    precio = Column(Numeric, nullable=False)
    num_porciones = Column(Integer)
    url_foto = Column(String)
    pct_prima_real = Column(Numeric)
    activo = Column(Boolean, default=True)
    fecha_lanzamiento = Column(Date, nullable=True)
    fecha_modificacion = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    categoria = relationship("Categoria", back_populates="productos")
    recetas = relationship("RecetaVersion", back_populates="producto")