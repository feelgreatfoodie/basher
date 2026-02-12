"""add last_checkpoint to analyses

Revision ID: 004
Revises: 003
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "analyses",
        sa.Column("last_checkpoint", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("analyses", "last_checkpoint")
