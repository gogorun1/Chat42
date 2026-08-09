from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.schemas.analytics import (
    AnalyticsSummaryOut,
    DailyTrendOut,
    TopReporterOut,
    ZoneActivityOut,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
async def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    reporter_limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),  # auth required, no role check
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummaryOut:
    # Computed in Python (not func.now() - interval) so the same query works
    # unchanged on SQLite in tests and Postgres in prod - date arithmetic
    # functions differ between the two dialects, a plain bound datetime doesn't.
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    total_sightings = await db.scalar(select(func.count()).select_from(Sighting)) or 0

    zone_rows = (
        await db.execute(
            select(Zone.id, Zone.name, func.count(Sighting.id))
            .join(Sighting, Sighting.zone_id == Zone.id)
            .where(Sighting.created_at >= window_start)
            .group_by(Zone.id, Zone.name)
            .order_by(func.count(Sighting.id).desc())
        )
    ).all()
    zone_activity = [
        ZoneActivityOut(zone_id=zid, zone_name=name, count=count)
        for zid, name, count in zone_rows
    ]

    trend_rows = (
        await db.execute(
            select(func.date(Sighting.created_at), func.count(Sighting.id))
            .where(Sighting.created_at >= window_start)
            .group_by(func.date(Sighting.created_at))
            .order_by(func.date(Sighting.created_at).asc())
        )
    ).all()
    daily_trend = [DailyTrendOut(date=str(date), count=count) for date, count in trend_rows]

    reporter_rows = (
        await db.execute(
            select(User.id, User.email, func.count(Sighting.id))
            .join(Sighting, Sighting.user_id == User.id)
            .group_by(User.id, User.email)
            .order_by(func.count(Sighting.id).desc())
            .limit(reporter_limit)
        )
    ).all()
    top_reporters = [
        TopReporterOut(user_id=uid, email=email, count=count)
        for uid, email, count in reporter_rows
    ]

    return AnalyticsSummaryOut(
        total_sightings=total_sightings,
        window_days=days,
        zone_activity=zone_activity,
        daily_trend=daily_trend,
        top_reporters=top_reporters,
    )