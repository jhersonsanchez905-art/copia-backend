"""apertura_caja: drop uq_apertura_usuario_turno_fecha to allow same-day shift reopening

The business requires a cashier to open → close → reopen within the same day and turn
(e.g. opens at 2pm, closes at 4pm, reopens at 4:10pm).  The previous constraint blocked
any second INSERT for the same (id_usuario, turno, fecha) with a DB-level error.

Flow control is now handled exclusively at the service layer:
  - abrir_caja raises 409 if there is already an *unclosed* apertura for this user.
  - Once the previous apertura is closed, get_apertura_sin_cierre returns None
    and a new apertura can be created freely.

Revision ID: 009
Revises: 686e54a3d226
Create Date: 2026-06-12
"""

from alembic import op

revision = "009"
down_revision = "686e54a3d226"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_apertura_usuario_turno_fecha",
        "apertura_caja",
        schema="pos",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_apertura_usuario_turno_fecha",
        "apertura_caja",
        ["id_usuario", "turno", "fecha"],
        schema="pos",
    )
