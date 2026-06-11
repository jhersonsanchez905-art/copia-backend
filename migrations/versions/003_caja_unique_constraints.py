"""caja: add unique constraints to prevent duplicate openings and duplicate payment methods

Revision ID: 003
Revises: 002
Create Date: 2026-06-11
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Prevents a cashier from opening two shifts for the same day and turn.
    op.create_unique_constraint(
        "uq_apertura_usuario_turno_fecha",
        "apertura_caja",
        ["id_usuario", "turno", "fecha"],
        schema="pos",
    )
    # Prevents the same payment method from appearing twice in a single closing.
    op.create_unique_constraint(
        "uq_cierre_detalle_metodo",
        "cierre_caja_detalle",
        ["id_cierre", "id_metodo_pago"],
        schema="pos",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_cierre_detalle_metodo", "cierre_caja_detalle", schema="pos"
    )
    op.drop_constraint(
        "uq_apertura_usuario_turno_fecha", "apertura_caja", schema="pos"
    )
