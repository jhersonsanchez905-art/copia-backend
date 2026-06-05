"""
proveedor.py
Modelos de proveedores e insumos-proveedor del sistema POS.
Autor: charlykj
Issue: #18
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Proveedor(Base):
    __tablename__ = "proveedor"
    __table_args__ = {"schema": "pos"}

    id_proveedor = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String)
    telefono = Column(String)
    correo = Column(String)
    activo = Column(Boolean, default=True)

    insumos = relationship("InsumoProveedor", back_populates="proveedor")
    ordenes_compra = relationship("OrdenCompra", back_populates="proveedor")


class InsumoProveedor(Base):
    __tablename__ = "insumo_proveedor"
    __table_args__ = {"schema": "pos"}

    id_insumo_proveedor = Column(Integer, primary_key=True, index=True)
    id_insumo = Column(Integer, ForeignKey("pos.insumo.id_insumo"), nullable=False)
    id_proveedor = Column(Integer, ForeignKey("pos.proveedor.id_proveedor"), nullable=False)
    es_principal = Column(Boolean, default=False)
    precio_referencia = Column(Numeric)
    dias_entrega = Column(Integer)

    proveedor = relationship("Proveedor", back_populates="insumos")
    insumo = relationship("Insumo", back_populates="proveedores")