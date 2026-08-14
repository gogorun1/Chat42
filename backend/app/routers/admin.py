from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.zone import Zone
from app.schemas.admin import ZoneCreate, ZoneUpdate
from app.schemas.sighting import ZoneRead

router = APIRouter(prefix="/admin", tags=["admin"])

moderator_or_admin = require_role(UserRole.MODERATOR, UserRole.ADMIN)
admin_only = require_role(UserRole.ADMIN)


@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: ZoneCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(moderator_or_admin),
) -> Zone:
    existing = await db.scalar(select(Zone).where(Zone.slug == payload.slug))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Zone slug already exists")

    zone = Zone(slug=payload.slug, name=payload.name)
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.patch("/zones/{zone_id}", response_model=ZoneRead)
async def update_zone(
    zone_id: int,
    payload: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(moderator_or_admin),
) -> Zone:
    zone = await db.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    if payload.slug is not None:
        zone.slug = payload.slug
    if payload.name is not None:
        zone.name = payload.name

    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(moderator_or_admin),
) -> None:
    zone = await db.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    await db.delete(zone)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Zone has sightings recorded against it and cannot be deleted",
        ) from exc
