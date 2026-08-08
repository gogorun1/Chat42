"""add zones and sightings tables

Revision ID: a1b2c3d4e5f6
Revises: 52125347147b
Create Date: 2026-08-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "52125347147b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CAMPUS_ZONES = [
    ("a-block", "A Block"),
    ("b-block", "B Block"),
    ("c-block", "C Block"),
    ("cluster", "Cluster"),
    ("outside", "Outside Campus"),
]


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_zones_slug"), "zones", ["slug"], unique=True)

    zones_table = sa.table(
        "zones",
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(zones_table, [{"slug": slug, "name": name} for slug, name in CAMPUS_ZONES])

    op.create_table(
        "sightings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sightings_user_id"), "sightings", ["user_id"], unique=False)
    op.create_index(op.f("ix_sightings_zone_id"), "sightings", ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sightings_zone_id"), table_name="sightings")
    op.drop_index(op.f("ix_sightings_user_id"), table_name="sightings")
    op.drop_table("sightings")
    op.drop_index(op.f("ix_zones_slug"), table_name="zones")
    op.drop_table("zones")
