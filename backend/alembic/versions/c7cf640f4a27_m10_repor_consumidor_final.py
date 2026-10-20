"""M10 repor consumidor_final

Revision ID: c7cf640f4a27
Revises: 8ffc2a1ea06d
Create Date: 2026-10-19

"""
from alembic import op
import sqlalchemy as sa


revision = "c7cf640f4a27"
down_revision = "8ffc2a1ea06d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "consumidor_final",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_column("consumidor_final")