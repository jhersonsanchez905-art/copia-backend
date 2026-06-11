"""caja: convert hora_apertura and hora_cierre to TIMESTAMPTZ

Revision ID: 002
Revises: 001
Create Date: 2026-06-11
"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "apertura_caja",
        "hora_apertura",
        type_=sa.DateTime(timezone=True),
        schema="pos",
        postgresql_using="hora_apertura AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "cierre_caja",
        "hora_cierre",
        type_=sa.DateTime(timezone=True),
        schema="pos",
        postgresql_using="hora_cierre AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "apertura_caja",
        "hora_apertura",
        type_=sa.DateTime(),
        schema="pos",
        postgresql_using="hora_apertura AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "cierre_caja",
        "hora_cierre",
        type_=sa.DateTime(),
        schema="pos",
        postgresql_using="hora_cierre AT TIME ZONE 'UTC'",
    )
