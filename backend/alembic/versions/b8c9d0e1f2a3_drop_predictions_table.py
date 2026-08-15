"""drop predictions table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2

The "guess tomorrow's zone" lazy-settlement design (predictions +
gamification_service.settle_pending_predictions) was built before
the 2026-08-15 decision to keep F4's guess-today, instant-judge
flow instead (backed by users.guess_points / POST
/gamification/guess). Nothing reads or writes this table anymore,
so it's removed rather than left as dead schema.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_predictions_user_id", table_name="predictions")
    op.drop_table("predictions")


def downgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "target_date"),
    )
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
