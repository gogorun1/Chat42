from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserRead
from app.schemas.users import ProfileUpdate
from app.services.storage import save_upload

router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


@router.patch("/me", response_model=UserRead)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    current_user.display_name = payload.display_name
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    content_type = avatar.content_type or ""
    content = await avatar.read()

    try:
        filename = save_upload(Path(settings.upload_dir), content, content_type)
    except ValueError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc

    current_user.avatar_path = filename
    await db.commit()
    await db.refresh(current_user)
    return current_user
