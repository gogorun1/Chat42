"""replace placeholder zones with F4's real campus zone list

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0

F2's original seed (a-block/b-block/c-block/cluster/outside) was a
placeholder that never matched F4's actual campus map
(frontend/src/components/42map.tsx), which models 13 real
floor/room zones with their own SVGs. This replaces the seed so
zone_id in the backend lines up with the slugs F4's map already
uses as keys (entrance, f0, f1, ...).

Old zones without sightings are removed. Referenced legacy zones are
kept because assigning those sightings to a new location would invent
location data. Predictions for removed zones cascade-delete via their
foreign key.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_ZONES = [
    ("a-block", "A Block"),
    ("b-block", "B Block"),
    ("c-block", "C Block"),
    ("cluster", "Cluster"),
    ("outside", "Outside Campus"),
]

OBSOLETE_ZONE_SLUGS = [slug for slug, _ in OLD_ZONES] + ["f4"]

NEW_ZONES = [
    ("entrance", "42 Entrance"),
    ("cantine_m1", "CantiSkate"),
    ("cantine_0", "Shokudo"),
    ("cantine_1", "La Piscine"),
    ("f0", "F0"),
    ("f1", "F1"),
    ("f1b", "F1b"),
    ("f2", "F2"),
    ("f6", "F6"),
    ("playroom", "Cafe avant la fin du monde"),
    ("roof2", "Terrase (2)"),
    ("roof3", "Terrase (3)"),
    ("stairs", "Stairs"),
]

zones_table = sa.table(
    "zones",
    sa.column("id", sa.Integer),
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
)

sightings_table = sa.table(
    "sightings",
    sa.column("zone_id", sa.Integer),
)


def replace_unreferenced_zones(zones_to_add: list[tuple[str, str]], slugs_to_remove: list[str]) -> None:
    statement = insert(zones_table).values(
        [{"slug": slug, "name": name} for slug, name in zones_to_add]
    )
    statement = statement.on_conflict_do_update(
        index_elements=[zones_table.c.slug],
        set_={"name": statement.excluded.name},
    )
    op.get_bind().execute(statement)

    referenced = sa.exists(
        sa.select(1).where(sightings_table.c.zone_id == zones_table.c.id)
    )
    op.get_bind().execute(
        sa.delete(zones_table)
        .where(zones_table.c.slug.in_(slugs_to_remove))
        .where(~referenced)
    )


def upgrade() -> None:
    replace_unreferenced_zones(NEW_ZONES, OBSOLETE_ZONE_SLUGS)


def downgrade() -> None:
    replace_unreferenced_zones(OLD_ZONES, [slug for slug, _ in NEW_ZONES] + ["f4"])
