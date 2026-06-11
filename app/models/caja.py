"""
app/models/caja.py

Cash register models: opening, closing, closing details, denominations catalogue,
and denomination breakdown for both opening and closing (arqueo).

Author: Suley Suarez
Issue: #21
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Denominacion ──────────────────────────────────────────────────────────────

class Denominacion(Base):
    """Master catalogue of valid bill and coin denominations."""
    __tablename__ = "denominacion"
    __table_args__ = {"schema": "pos"}

    id_denominacion = Column(Integer, primary_key=True, index=True)
    valor           = Column(Numeric(14, 2), nullable=False, unique=True)
    tipo            = Column(String(10), nullable=False)   # "billete" | "moneda"
    activo          = Column(Boolean, nullable=False, default=True)


# ── AperturaCaja ──────────────────────────────────────────────────────────────

class AperturaCaja(Base):
    __tablename__ = "apertura_caja"
    __table_args__ = {"schema": "pos"}

    id_apertura   = Column(Integer, primary_key=True, index=True)
    id_usuario    = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    turno         = Column(String, nullable=False)
    fecha         = Column(Date, nullable=False)
    monto_inicial = Column(Numeric(16, 2), nullable=False)
    hora_apertura = Column(DateTime(timezone=True), default=_utcnow)
    observaciones = Column(String)

    ventas = relationship("Venta", back_populates="apertura")
    cierre = relationship("CierreCaja", back_populates="apertura", uselist=False)
    arqueo = relationship(
        "AperturaCajaArqueo",
        back_populates="apertura",
        cascade="all, delete-orphan",
    )


class AperturaCajaArqueo(Base):
    """Denomination breakdown recorded when opening a cash register shift."""
    __tablename__ = "apertura_caja_arqueo"
    __table_args__ = (
        UniqueConstraint("id_apertura", "id_denominacion", name="uq_apertura_denominacion"),
        {"schema": "pos"},
    )

    id_arqueo       = Column(Integer, primary_key=True, index=True)
    id_apertura     = Column(Integer, ForeignKey("pos.apertura_caja.id_apertura"), nullable=False)
    id_denominacion = Column(Integer, ForeignKey("pos.denominacion.id_denominacion"), nullable=False)
    cantidad        = Column(Integer, nullable=False)
    subtotal        = Column(Numeric(16, 2), nullable=False)  # cantidad × valor

    apertura     = relationship("AperturaCaja", back_populates="arqueo")
    denominacion = relationship("Denominacion")


# ── CierreCaja ────────────────────────────────────────────────────────────────

class CierreCaja(Base):
    __tablename__ = "cierre_caja"
    __table_args__ = {"schema": "pos"}

    id_cierre           = Column(Integer, primary_key=True, index=True)
    id_apertura         = Column(Integer, ForeignKey("pos.apertura_caja.id_apertura"), nullable=False, unique=True)
    id_usuario          = Column(Integer, ForeignKey("pos.usuario.id_usuario"), nullable=False)
    turno               = Column(String)
    fecha               = Column(Date)
    total_general       = Column(Numeric(16, 2))
    total_transacciones = Column(Numeric(16, 2))
    diferencia          = Column(Numeric(16, 2))
    hora_cierre         = Column(DateTime(timezone=True), default=_utcnow)
    observaciones       = Column(String)

    apertura        = relationship("AperturaCaja", back_populates="cierre")
    detalle         = relationship("CierreCajaDetalle", back_populates="cierre", cascade="all, delete-orphan")
    arqueo_efectivo = relationship(
        "CierreCajaArqueo",
        back_populates="cierre",
        cascade="all, delete-orphan",
    )


class CierreCajaDetalle(Base):
    __tablename__ = "cierre_caja_detalle"
    __table_args__ = {"schema": "pos"}

    id_detalle      = Column(Integer, primary_key=True, index=True)
    id_cierre       = Column(Integer, ForeignKey("pos.cierre_caja.id_cierre"), nullable=False)
    id_metodo_pago  = Column(Integer, ForeignKey("pos.metodo_pago.id_metodo_pago"), nullable=False)
    total_esperado  = Column(Numeric(16, 2))
    total_contado   = Column(Numeric(16, 2))
    diferencia      = Column(Numeric(16, 2))

    cierre = relationship("CierreCaja", back_populates="detalle")


class CierreCajaArqueo(Base):
    """Denomination breakdown recorded when closing a cash register shift."""
    __tablename__ = "cierre_caja_arqueo"
    __table_args__ = (
        UniqueConstraint("id_cierre", "id_denominacion", name="uq_cierre_denominacion"),
        {"schema": "pos"},
    )

    id_arqueo       = Column(Integer, primary_key=True, index=True)
    id_cierre       = Column(Integer, ForeignKey("pos.cierre_caja.id_cierre"), nullable=False)
    id_denominacion = Column(Integer, ForeignKey("pos.denominacion.id_denominacion"), nullable=False)
    cantidad        = Column(Integer, nullable=False)
    subtotal        = Column(Numeric(16, 2), nullable=False)  # cantidad × valor

    cierre       = relationship("CierreCaja", back_populates="arqueo_efectivo")
    denominacion = relationship("Denominacion")
