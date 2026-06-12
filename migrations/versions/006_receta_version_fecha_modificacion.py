"""receta_version: add fecha_modificacion column

Revision ID: 006
Revises: 005
Create Date: 2026-06-11
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "receta_version",
        sa.Column("fecha_modificacion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )


def downgrade() -> None:
    op.drop_column("receta_version", "fecha_modificacion", schema="pos")
