"""replace placeholder zones with F4's real campus zone list

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0

F2's original seed (a-block/b-block/c-block/cluster/outside) was a
placeholder that never matched F4's actual campus map
(frontend/src/components/42map.tsx), which models 13 real
floor/room zones with their own SVGs. This replaces the seed so
zone_id in the backend lines up with the slugs F4's map already
uses as keys (entrance, f0, f1, ...).

No existing sightings reference the old zones (checked: 0 rows in
`sightings` as of this migration), so this is a straight swap, not
a data migration. The one pre-existing test `predictions` row
cascade-deletes with its zone via the FK's ON DELETE CASCADE.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

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
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
)


def upgrade() -> None:
    op.execute("DELETE FROM zones")
    op.bulk_insert(zones_table, [{"slug": slug, "name": name} for slug, name in NEW_ZONES])


def downgrade() -> None:
    op.execute("DELETE FROM zones")
    op.bulk_insert(zones_table, [{"slug": slug, "name": name} for slug, name in OLD_ZONES])
