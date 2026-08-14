from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_role
from app.models.sighting import Sighting
from app.models.user import User, UserRole
from app.models.zone import Zone
from app.schemas.admin import AdminUserRead, SightingZoneUpdate, UserRoleUpdate, ZoneCreate, ZoneUpdate
from app.schemas.sighting import SightingRead, ZoneRead

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


@router.patch("/sightings/{sighting_id}", response_model=SightingRead)
async def reassign_sighting_zone(
    sighting_id: int,
    payload: SightingZoneUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(moderator_or_admin),
) -> SightingRead:
    sighting = await db.get(Sighting, sighting_id, options=[selectinload(Sighting.zone)])
    if sighting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sighting not found")

    zone = await db.get(Zone, payload.zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    sighting.zone_id = zone.id
    await db.commit()
    await db.refresh(sighting)
    return _to_sighting_read(sighting, zone)


@router.delete("/sightings/{sighting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sighting(
    sighting_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(moderator_or_admin),
) -> None:
    sighting = await db.get(Sighting, sighting_id)
    if sighting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sighting not found")

    await db.delete(sighting)
    await db.commit()


def _to_sighting_read(sighting: Sighting, zone: Zone) -> SightingRead:
    return SightingRead(
        id=sighting.id,
        zone_id=sighting.zone_id,
        image_url=f"/uploads/{sighting.image_path}",
        created_at=sighting.created_at,
        zone=zone,
    )


@router.get("/users", response_model=list[AdminUserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/role", response_model=AdminUserRead)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
) -> User:
    if user_id == current_user.id and payload.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot change your own role")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return user
