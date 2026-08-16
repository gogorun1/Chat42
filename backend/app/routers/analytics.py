from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.sighting import Sighting
from app.models.user import User, UserRole
from app.models.zone import Zone
from app.schemas.analytics import (
    AnalyticsSummaryOut,
    DailyTrendOut,
    TopReporterOut,
    ZoneActivityOut,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

moderator_or_admin = require_role(UserRole.MODERATOR, UserRole.ADMIN)


@router.get("/summary", response_model=AnalyticsSummaryOut)
async def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    zone_id: int | None = Query(default=None),
    reporter_limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(moderator_or_admin),
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

    # date_to already arrives as the end of the selected day (23:59:59), so
    # it's used as an inclusive upper bound rather than pushed a day further.
    window_end = date_to

    def apply_filters(stmt):
        stmt = stmt.where(Sighting.created_at >= window_start)
        if window_end is not None:
            stmt = stmt.where(Sighting.created_at <= window_end)
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

    reporter_stmt = apply_filters(
        select(
            User.id,
            User.email,
            User.display_name,
            func.count(Sighting.id))
        .join(Sighting, Sighting.user_id == User.id)
    ).group_by(
        User.id, User.email, User.display_name
    ).order_by(
        func.count(Sighting.id).desc()
    ).limit(reporter_limit)

    reporter_rows = (await db.execute(reporter_stmt)).all()
    top_reporters = [
        TopReporterOut(user_id=uid, email=email, display_name=display_name, count=count)
        for uid, email, display_name, count in reporter_rows
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
    )
