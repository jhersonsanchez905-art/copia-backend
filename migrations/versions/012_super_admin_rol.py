"""rol: add super_admin

Adds the 'super_admin' role, which has unrestricted access to every
endpoint (see app/dependencies/roles.py::require_rol) and is the only
role allowed to manage other administrators.

Revision ID: 012
Revises: 011
Create Date: 2026-06-13
"""

from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO pos.rol (nombre, descripcion)
        SELECT 'super_admin', 'Acceso total al sistema, incluida la gestión de administradores'
        WHERE NOT EXISTS (
            SELECT 1 FROM pos.rol WHERE nombre = 'super_admin'
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM pos.rol WHERE nombre = 'super_admin'")
