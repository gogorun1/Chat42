from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.schemas.sighting import SightingRead, ZoneRead
from app.services.cat_detection import InvalidImageError
from app.services.storage import save_upload
from app.services.stub_cat_detector import get_cat_detector

router = APIRouter(prefix="/sightings", tags=["sightings"])
settings = get_settings()


@router.get("/zones", response_model=list[ZoneRead])
async def list_zones(db: AsyncSession = Depends(get_db)) -> list[Zone]:
    result = await db.execute(select(Zone).order_by(Zone.name))
    return list(result.scalars().all())


@router.get("/", response_model=list[SightingRead])
async def list_sightings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SightingRead]:
    result = await db.execute(
        select(Sighting)
        .where(Sighting.user_id == current_user.id)
        .options(selectinload(Sighting.zone))
        .order_by(Sighting.created_at.desc())
    )
    sightings = result.scalars().all()
    return [_to_sighting_read(sighting) for sighting in sightings]


@router.post("/", response_model=SightingRead, status_code=status.HTTP_201_CREATED)
async def create_sighting(
    zone_id: int = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SightingRead:
    zone = await db.get(Zone, zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    content_type = image.content_type or ""
    if content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only JPEG, PNG, WebP, and GIF images are allowed")

    content = await image.read()
    detector = get_cat_detector()

    try:
        detection = detector.detect(content)
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    if not detection.is_cat:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No cat detected in this image. Please upload a photo that clearly shows a cat.",
        )

    try:
        filename = save_upload(Path(settings.upload_dir), content, content_type)
    except ValueError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc

    sighting = Sighting(user_id=current_user.id, zone_id=zone.id, image_path=filename)
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)
    sighting.zone = zone
    return _to_sighting_read(sighting)


def _to_sighting_read(sighting: Sighting) -> SightingRead:
    return SightingRead(
        id=sighting.id,
        zone_id=sighting.zone_id,
        image_url=f"/uploads/{sighting.image_path}",
        created_at=sighting.created_at,
        zone=sighting.zone,
    )
