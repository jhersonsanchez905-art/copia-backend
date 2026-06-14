"""metodo_pago: merge Nequi/Daviplata into Transferencia

Both 'Nequi' and 'Daviplata' are bank transfers and are now covered by
the generic 'Transferencia' method. Existing 'pago' rows referencing
either are reassigned to 'Transferencia', then the now-unused
'Nequi'/'Daviplata' rows are removed from 'metodo_pago'.

Note: downgrade recreates the 'Nequi'/'Daviplata' rows but cannot
restore which 'pago' rows originally pointed to them.

Revision ID: 014
Revises: 013
Create Date: 2026-06-13
"""

from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO pos.metodo_pago (nombre, requiere_comprobante, activo)
        SELECT 'Transferencia', true, true
        WHERE NOT EXISTS (
            SELECT 1 FROM pos.metodo_pago WHERE nombre = 'Transferencia'
        )
        """
    )
    op.execute(
        """
        UPDATE pos.pago
        SET id_metodo_pago = (
            SELECT id_metodo_pago FROM pos.metodo_pago WHERE nombre = 'Transferencia'
        )
        WHERE id_metodo_pago IN (
            SELECT id_metodo_pago FROM pos.metodo_pago WHERE nombre IN ('Nequi', 'Daviplata')
        )
        """
    )
    op.execute("DELETE FROM pos.metodo_pago WHERE nombre IN ('Nequi', 'Daviplata')")


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO pos.metodo_pago (nombre, requiere_comprobante, activo)
        SELECT 'Nequi', true, true
        WHERE NOT EXISTS (
            SELECT 1 FROM pos.metodo_pago WHERE nombre = 'Nequi'
        )
        """
    )
    op.execute(
        """
        INSERT INTO pos.metodo_pago (nombre, requiere_comprobante, activo)
        SELECT 'Daviplata', true, true
        WHERE NOT EXISTS (
            SELECT 1 FROM pos.metodo_pago WHERE nombre = 'Daviplata'
        )
        """
    )
