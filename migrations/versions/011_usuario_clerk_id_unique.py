"""usuario: unique constraint on clerk_id

Prevents duplicate rows when the client calls /auth/register concurrently
(React StrictMode double-effect, network retries, etc.).
Existing duplicates are resolved by keeping the earliest id_usuario per clerk_id.

Revision ID: 011
Revises: 010
Create Date: 2026-06-13
"""


from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove any existing duplicates, keeping the earliest row per clerk_id.
    op.execute(
        """
        DELETE FROM pos.usuario
        WHERE id_usuario NOT IN (
            SELECT MIN(id_usuario)
            FROM pos.usuario
            GROUP BY clerk_id
        )
        """
    )
    op.create_unique_constraint(
        "uq_usuario_clerk_id",
        "usuario",
        ["clerk_id"],
        schema="pos",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_usuario_clerk_id",
        "usuario",
        schema="pos",
        type_="unique",
    )
