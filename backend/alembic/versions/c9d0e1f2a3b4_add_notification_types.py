"""add sighting_removed and role_changed to notification_type enum

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLAlchemy's Enum(SomePyEnum) binds on the Python enum MEMBER NAME,
    # not .value -- confirmed by b2c3d4e5f6a7's enum labels being
    # uppercase ("SIGHTING_NEARBY", "BADGE_EARNED", etc.), matching
    # NotificationType's member names. New labels follow the same
    # convention.
    #
    # ALTER TYPE ... ADD VALUE must not share a transaction with other
    # DDL on some Postgres versions -- this migration does nothing else,
    # intentionally.
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'SIGHTING_REMOVED'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ROLE_CHANGED'")


def downgrade() -> None:
    # Postgres does not support removing individual enum values without
    # recreating the type and remapping the column -- left as a manual
    # step if ever needed.
    pass