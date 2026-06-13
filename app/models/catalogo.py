"""
catalogo.py
Modelos de catálogo base del sistema POS: roles, usuarios, clientes,
marcas, unidades de medida, clasificaciones, categorías y métodos de pago.
Autor: charlykj
Issue: #18
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime


class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = {"schema": "pos"}

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "pos"}

    id_usuario = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, nullable=False, unique=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=False)
    id_rol = Column(Integer, ForeignKey("pos.rol.id_rol"))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    rol = relationship("Rol", back_populates="usuarios")
    ventas = relationship("Venta", back_populates="usuario", foreign_keys="Venta.id_usuario")
    ordenes_compra = relationship("OrdenCompra", back_populates="usuario")
    reservas = relationship("Reserva", back_populates="usuario")
    pedidos = relationship("Pedido", back_populates="usuario")


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = {"schema": "pos"}

    id_cliente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String)
    telefono = Column(String)
    correo = Column(String)
    direccion = Column(String)
    numero_documento = Column(String)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)
    activo = Column(Boolean, default=True)
    observaciones = Column(String)

    ventas = relationship("Venta", back_populates="cliente")
    reservas = relationship("Reserva", back_populates="cliente")


class Marca(Base):
    __tablename__ = "marca"
    __table_args__ = {"schema": "pos"}

    id_marca = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

    insumos = relationship("Insumo", back_populates="marca")


class UnidadMedida(Base):
    __tablename__ = "unidad_medida"
    __table_args__ = {"schema": "pos"}

    id_unidad = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    abreviatura = Column(String, nullable=False)

    insumos = relationship("Insumo", back_populates="unidad")


class Clasificacion(Base):
    __tablename__ = "clasificacion"
    __table_args__ = {"schema": "pos"}

    id_clasificacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)

    insumos = relationship("Insumo", back_populates="clasificacion")


class Categoria(Base):
    __tablename__ = "categoria"
    __table_args__ = {"schema": "pos"}

    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

    productos = relationship("Producto", back_populates="categoria")


class MetodoPago(Base):
    __tablename__ = "metodo_pago"
    __table_args__ = {"schema": "pos"}

    id_metodo_pago = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    requiere_comprobante = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)

    pagos = relationship("Pago", back_populates="metodo_pago")
    