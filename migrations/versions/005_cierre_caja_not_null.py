"""caja: enforce NOT NULL on cierre_caja and cierre_caja_detalle financial columns

Revision ID: 005
Revises: 004
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in ("turno", "fecha", "total_general", "total_transacciones", "diferencia", "hora_cierre"):
        op.alter_column("cierre_caja", col, nullable=False, schema="pos")

    for col in ("total_esperado", "total_contado", "diferencia"):
        op.alter_column("cierre_caja_detalle", col, nullable=False, schema="pos")


def downgrade() -> None:
    for col in ("turno", "fecha", "total_general", "total_transacciones", "diferencia", "hora_cierre"):
        op.alter_column("cierre_caja", col, nullable=True, schema="pos")

    for col in ("total_esperado", "total_contado", "diferencia"):
        op.alter_column("cierre_caja_detalle", col, nullable=True, schema="pos")
