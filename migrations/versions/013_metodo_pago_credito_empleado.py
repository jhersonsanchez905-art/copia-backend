"""metodo_pago: add Credito empleado

Adds the 'Crédito empleado' payment method, used when an employee
consumes a product and pays for it later (a tab/fiado), instead of
paying at the time of the sale.

Revision ID: 013
Revises: 012
Create Date: 2026-06-13
"""

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO pos.metodo_pago (nombre, requiere_comprobante, activo)
        SELECT 'Crédito empleado', false, true
        WHERE NOT EXISTS (
            SELECT 1 FROM pos.metodo_pago WHERE nombre = 'Crédito empleado'
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM pos.metodo_pago WHERE nombre = 'Crédito empleado'")
