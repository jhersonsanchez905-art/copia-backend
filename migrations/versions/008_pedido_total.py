"""pedido: add total column

Revision ID: 008
Revises: 007
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pedido",
        sa.Column(
            "total",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0",
        ),
        schema="pos",
    )


def downgrade() -> None:
    op.drop_column("pedido", "total", schema="pos")
