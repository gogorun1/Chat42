"""add role to users

Revision ID: 8fcd40c52b1e
Revises: c3d4e5f6a7b8
Create Date: 2026-08-14 15:03:06.963504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8fcd40c52b1e'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM(
    "USER", "MODERATOR", "ADMIN", name="user_role", create_type=False
)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("role", user_role, server_default="USER", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    user_role.drop(op.get_bind(), checkfirst=True)
