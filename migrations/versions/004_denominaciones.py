"""caja: add denomination catalogue and arqueo tables for opening/closing cash count

Revision ID: 004
Revises: 003
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

# Colombian Peso denominations (COP).
# $1,000 COP exists as both coin and bill; the unique constraint on valor keeps
# only one entry — recorded as moneda (coin) since it is more common in cash counts.
_DENOMINACIONES = [
    # monedas
    {"valor": "50",     "tipo": "moneda"},
    {"valor": "100",    "tipo": "moneda"},
    {"valor": "200",    "tipo": "moneda"},
    {"valor": "500",    "tipo": "moneda"},
    {"valor": "1000",   "tipo": "moneda"},
    # billetes
    {"valor": "2000",   "tipo": "billete"},
    {"valor": "5000",   "tipo": "billete"},
    {"valor": "10000",  "tipo": "billete"},
    {"valor": "20000",  "tipo": "billete"},
    {"valor": "50000",  "tipo": "billete"},
    {"valor": "100000", "tipo": "billete"},
    {"valor": "200000", "tipo": "billete"},
]


def upgrade() -> None:
    # ── denominacion ─────────────────────────────────────────────────────────
    op.create_table(
        "denominacion",
        sa.Column("id_denominacion", sa.Integer(), primary_key=True),
        sa.Column("valor", sa.Numeric(14, 2), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("valor", name="uq_denominacion_valor"),
        schema="pos",
    )

    # ── apertura_caja_arqueo ──────────────────────────────────────────────────
    op.create_table(
        "apertura_caja_arqueo",
        sa.Column("id_arqueo", sa.Integer(), primary_key=True),
        sa.Column(
            "id_apertura",
            sa.Integer(),
            sa.ForeignKey("pos.apertura_caja.id_apertura", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "id_denominacion",
            sa.Integer(),
            sa.ForeignKey("pos.denominacion.id_denominacion"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=False),
        sa.UniqueConstraint(
            "id_apertura", "id_denominacion", name="uq_apertura_denominacion"
        ),
        schema="pos",
    )

    # ── cierre_caja_arqueo ────────────────────────────────────────────────────
    op.create_table(
        "cierre_caja_arqueo",
        sa.Column("id_arqueo", sa.Integer(), primary_key=True),
        sa.Column(
            "id_cierre",
            sa.Integer(),
            sa.ForeignKey("pos.cierre_caja.id_cierre", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "id_denominacion",
            sa.Integer(),
            sa.ForeignKey("pos.denominacion.id_denominacion"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=False),
        sa.UniqueConstraint(
            "id_cierre", "id_denominacion", name="uq_cierre_denominacion"
        ),
        schema="pos",
    )

    # ── seed Colombian Peso denominations ────────────────────────────────────
    rows = ", ".join(
        f"({d['valor']}, '{d['tipo']}', true)" for d in _DENOMINACIONES
    )
    op.execute(
        sa.text(f"INSERT INTO pos.denominacion (valor, tipo, activo) VALUES {rows}")
    )


def downgrade() -> None:
    op.drop_table("cierre_caja_arqueo", schema="pos")
    op.drop_table("apertura_caja_arqueo", schema="pos")
    op.drop_table("denominacion", schema="pos")
