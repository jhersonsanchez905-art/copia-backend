"""venta: make id_pedido nullable for counter (mostrador) sales

Revision ID: 007
Revises: 006
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "venta",
        "id_pedido",
        existing_type=sa.Integer(),
        nullable=True,
        schema="pos",
    )


def downgrade() -> None:
    op.alter_column(
        "venta",
        "id_pedido",
        existing_type=sa.Integer(),
        nullable=False,
        schema="pos",
    )
