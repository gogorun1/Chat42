from __future__ import annotations

import argparse
import asyncio
import base64
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone

DUMMY_EMAILS = [
    "seed-alice@example.com",
    "seed-bob@example.com",
    "seed-chen@example.com",
    "seed-diego@example.com",
    "seed-fatima@example.com",
]

# A tiny valid 1x1 JPEG, base64-encoded, so seeded sightings have something
# real to point at instead of a broken <img> icon in the frontend. Every
# seeded sighting shares this one file.
_PLACEHOLDER_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkI"
    "CQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQ"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX"
    "/9k="
)


async def _ensure_placeholder_image() -> str:
    upload_dir = Path(get_settings().upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = "seed-placeholder.jpg"
    path = upload_dir / filename
    if not path.exists():
        path.write_bytes(base64.b64decode(_PLACEHOLDER_JPEG_B64))
    return filename


async def main(count: int) -> None:
    image_filename = await _ensure_placeholder_image()

    async with async_session_factory() as db:
        zones = (await db.scalars(select(Zone))).all()
        if not zones:
            raise SystemExit("No zones found - run the F2 migration before seeding sightings.")

        existing_users = (await db.scalars(select(User))).all()
        existing_emails = {u.email for u in existing_users}

        new_users = []
        for email in DUMMY_EMAILS:
            if email not in existing_emails:
                new_users.append(User(email=email, password_hash=None))
        if new_users:
            db.add_all(new_users)
            await db.commit()
            for u in new_users:
                await db.refresh(u)

        reporters = existing_users + new_users
        if not reporters:
            raise SystemExit("No users available to seed sightings for.")

        now = datetime.now(timezone.utc)
        sightings = []
        for _ in range(count):
            sighting = Sighting(
                user_id=random.choice(reporters).id,
                zone_id=random.choice(zones).id,
                image_path=image_filename,
            )
            # Spread across the last 60 days, weighted toward more recent
            # days, so the daily trend chart has some visible shape rather
            # than a flat uniform scatter.
            days_ago = int(random.triangular(0, 60, 5))
            sighting.created_at = now - timedelta(
                days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59)
            )
            sightings.append(sighting)

        db.add_all(sightings)
        await db.commit()

        print(f"Seeded {len(sightings)} sightings across {len(zones)} zones and {len(reporters)} reporters.")
        print(f"({len(new_users)} new dummy users created; {len(existing_users)} existing users reused.)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=50, help="Number of sightings to create (default: 50)")
    args = parser.parse_args()
    asyncio.run(main(args.count))