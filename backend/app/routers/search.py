from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.schemas.search import SightingSearchOut, SightingSearchResult, SightingSortField, SortOrder

router = APIRouter(prefix="/api/search", tags=["search"])

SORT_COLUMN = {
    SightingSortField.CREATED_AT: Sighting.created_at,
    SightingSortField.ZONE: Zone.name,
}

@router.get("/sightings", response_model=SightingSearchResult)
async def search_sightings(
    zone_id: int | None = Query(None),
    user_id: int | None = Query(None, description="Filter by reporter"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    sort_by: SightingSortField = Query(SightingSortField.CREATED_AT),
    sort_order: SortOrder = Query(SortOrder.DESC),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SightingSearchResult:
    stmt = (
        select(Sighting)
        .join(Zone, Sighting.zone_id == Zone.id)
        .join(User, Sighting.user_id == User.id)
        .options(selectinload(Sighting.zone), selectinload(Sighting.user))
    )

    if zone_id is not None:
        stmt = stmt.where(Sighting.zone_id == zone_id)
    if user_id is not None:
        stmt = stmt.where(Sighting.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(Sighting.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Sighting.created_at <= date_to)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))

    order_col = SORT_COLUMN[sort_by]
    order_col = order_col.desc() if sort_order == SortOrder.DESC else order_col.asc()
    stmt = stmt.order_by(order_col).offset((page - 1) * page_size).limit(page_size)

    rows = (await db.scalars(stmt)).unique().all()

    items = [
        SightingSearchOut(
            id=s.id,
            zone_id=s.zone_id,
            zone_name=s.zone.name,
            reporter_id=s.user_id,
            reporter_email=s.user.email,
            image_url=f"/uploads/{s.image_path}",
            created_at=s.created_at,
        )
        for s in rows
    ]

    return SightingSearchResult(items=items, total=total or 0, page=page, page_size=page_size)