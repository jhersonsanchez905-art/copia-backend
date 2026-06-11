"""merge heads before bi schema

Revision ID: 2c4001937e5e
Revises: 7d3f406e43b4, abf4a4a8d52a
Create Date: 2026-06-11 10:13:13.932218
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2c4001937e5e'
down_revision = ('7d3f406e43b4', 'abf4a4a8d52a')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
