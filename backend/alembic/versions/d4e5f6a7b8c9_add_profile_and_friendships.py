"""add profile fields and friendships table

Revision ID: d4e5f6a7b8c9
Revises: 8fcd40c52b1e
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "8fcd40c52b1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

friendship_status = postgresql.ENUM(
    "PENDING", "ACCEPTED", name="friendship_status", create_type=False
)


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("avatar_path", sa.String(length=255), nullable=True))

    friendship_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("addressee_id", sa.Integer(), nullable=False),
        sa.Column("status", friendship_status, server_default="PENDING", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_id", "addressee_id"),
    )
    op.create_index(op.f("ix_friendships_requester_id"), "friendships", ["requester_id"])
    op.create_index(op.f("ix_friendships_addressee_id"), "friendships", ["addressee_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_friendships_addressee_id"), table_name="friendships")
    op.drop_index(op.f("ix_friendships_requester_id"), table_name="friendships")
    op.drop_table("friendships")
    friendship_status.drop(op.get_bind(), checkfirst=True)

    op.drop_column("users", "avatar_path")
    op.drop_column("users", "display_name")
