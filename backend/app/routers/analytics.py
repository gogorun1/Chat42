from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    RecentSightingOut
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
async def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    zone_id: int | None = Query(default=None),
    reporter_limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummaryOut:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from must be before date_to",
        )

    window_start = (date_from
        if date_from is not None
        else datetime.now(timezone.utc) - timedelta(days=days)
    )

    window_end = None
    if date_to is not None:
        window_end = date_to + timedelta(days=1)

    def apply_filters(stmt):
        stmt = stmt.where(Sighting.created_at >= window_start)
        if window_end is not None:
            stmt = stmt.where(Sighting.created_at < window_end)
        if zone_id is not None:
            stmt = stmt.where(Sighting.zone_id == zone_id)
        return stmt

    total_sightings = await db.scalar(select(func.count()).select_from(Sighting)) or 0

    period_count_stmt = apply_filters(
        select(func.count()).select_from(Sighting)
    )
    period_sightings = await db.scalar(period_count_stmt) or 0

    zone_stmt = apply_filters(
        select(
            Zone.id,
            Zone.name,
            func.count(Sighting.id),
        ).join(Sighting, Sighting.zone_id == Zone.id)
    ).group_by(Zone.id, Zone.name).order_by(func.count(Sighting.id).desc())

    zone_rows = (await db.execute(zone_stmt)).all()
    zone_activity = [
        ZoneActivityOut(zone_id=zid, zone_name=name, count=count)
        for zid, name, count in zone_rows
    ]

    trend_stmt = apply_filters(
        select(
            func.date(Sighting.created_at),
            func.count(Sighting.id),
        )
    ).group_by(
        func.date(Sighting.created_at)
    ).order_by(
        func.date(Sighting.created_at).asc()
    )

    trend_rows = (await db.execute(trend_stmt)).all()
    daily_trend = [
        DailyTrendOut(date=str(date), count=count)
        for date, count in trend_rows
    ]

    reporter_stmt = (
    # apply_filters(
        select(
            User.id,
            User.email,
            func.count(Sighting.id))
        .join(Sighting, Sighting.user_id == User.id)
    # )
        .group_by(User.id, User.email)
        .order_by(func.count(Sighting.id).desc())
        .limit(reporter_limit)
    )

    reporter_rows = (await db.execute(reporter_stmt)).all()
    top_reporters = [
        TopReporterOut(user_id=uid, email=email, count=count)
        for uid, email, count in reporter_rows
    ]

    recent_stmt = (
        apply_filters(
            select(Sighting)
            .options(
                selectinload(Sighting.zone),
                selectinload(Sighting.user),
            )
        )
        .order_by(Sighting.created_at.desc())
        .limit(10)
    )

    recent_rows = (await db.scalars(recent_stmt)).unique().all()

    recent_sightings = [
        RecentSightingOut(
            id=s.id,
            zone_id=s.zone_id,
            zone_name=s.zone.name,
            reporter=s.user.display_name or s.user.email.split("@")[0],
            image_url=f"/uploads/{s.image_path}",
            created_at=s.created_at,
        )
        for s in recent_rows
    ]
    return AnalyticsSummaryOut(
        total_sightings=total_sightings,
        period_sightings=period_sightings,
        window_start=window_start.date().isoformat(),
        window_end=(
            date_to.date().isoformat()
            if date_to is not None
            else None
        ),
        zone_activity=zone_activity,
        daily_trend=daily_trend,
        top_reporters=top_reporters,
        recent_sightings=recent_sightings
    )
