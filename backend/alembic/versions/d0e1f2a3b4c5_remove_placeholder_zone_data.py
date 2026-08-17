"""remove obsolete placeholder zone data

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OBSOLETE_ZONE_SLUGS = [
    "a-block",
    "b-block",
    "c-block",
    "cluster",
    "outside",
    "f4",
]

zones_table = sa.table(
    "zones",
    sa.column("id", sa.Integer),
    sa.column("slug", sa.String),
)

sightings_table = sa.table(
    "sightings",
    sa.column("zone_id", sa.Integer),
)


def upgrade() -> None:
    obsolete_zone_ids = sa.select(zones_table.c.id).where(
        zones_table.c.slug.in_(OBSOLETE_ZONE_SLUGS)
    )
    op.get_bind().execute(
        sa.delete(sightings_table).where(sightings_table.c.zone_id.in_(obsolete_zone_ids))
    )
    op.get_bind().execute(
        sa.delete(zones_table).where(zones_table.c.slug.in_(OBSOLETE_ZONE_SLUGS))
    )


def downgrade() -> None:
    # Deleted sighting data cannot be reconstructed truthfully.
    pass
