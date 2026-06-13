"""venta: add token_idempotencia for idempotent sale creation

When the frontend provides this token, repeated submissions (double-click,
browser retry, network timeout) with the same token return the original
completed sale instead of creating a duplicate.

The column is nullable (existing sales have no token) and carries a UNIQUE
constraint + index so the DB is the final arbiter under concurrent requests.

Revision ID: 010
Revises: 009
Create Date: 2026-06-12
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "venta",
        sa.Column("token_idempotencia", sa.String(64), nullable=True),
        schema="pos",
    )
    op.create_unique_constraint(
        "uq_venta_token_idempotencia",
        "venta",
        ["token_idempotencia"],
        schema="pos",
    )
    op.create_index(
        "ix_venta_token_idempotencia",
        "venta",
        ["token_idempotencia"],
        schema="pos",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_venta_token_idempotencia",
        table_name="venta",
        schema="pos",
    )
    op.drop_constraint(
        "uq_venta_token_idempotencia",
        "venta",
        schema="pos",
        type_="unique",
    )
    op.drop_column("venta", "token_idempotencia", schema="pos")
