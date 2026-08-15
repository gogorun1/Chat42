"""add guess_points to users

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1

Backs the "guess where the cat is" instant-judge game (F4's
handleGuess logic, kept as-is per the 2026-08-15 guess-today
decision) with a real, persisted point balance instead of
component-local state that reset on every page refresh. Starting
balance is 5, not F4's original mock value of 120.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("guess_points", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("users", "guess_points")
