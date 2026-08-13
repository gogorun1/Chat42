from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sighting import Sighting
from app.models.zone import Zone


@dataclass
class ZoneCount:
    name: str
    count: int


# the only content that llm can read from our database
@dataclass
class SightingContext:
    date: str
    total_sightings: int
    zones: list[ZoneCount] = field(default_factory=list)
    hours: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# core function for llm to create mollinette diary
async def build_daily_context(db: AsyncSession, day: date) -> SightingContext:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    zone_result = await db.execute(
        select(Zone.name, func.count(Sighting.id))
        .join(Sighting, Sighting.zone_id == Zone.id)
        .where(Sighting.created_at >= start, Sighting.created_at < end)
        .group_by(Zone.name)
        .order_by(func.count(Sighting.id).desc())
    )
    zones = [ZoneCount(name, count) for name, count in zone_result.all()]

    hour_result = await db.execute(
        select(func.extract("hour", Sighting.created_at)).where(
            Sighting.created_at >= start, Sighting.created_at < end
        )
    )
    hours = sorted({int(hour) for (hour,) in hour_result.all()})

    return SightingContext(
        date=day.isoformat(),
        total_sightings=sum(zone.count for zone in zones),
        zones=zones,
        hours=hours,
    )
