from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationListOut, NotificationOut
from datetime import datetime, timezone

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListOut:
    base_stmt = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        base_stmt = base_stmt.where(Notification.read_at.is_(None))

    total = await db.scalar(select(func.count()).select_from(base_stmt.subquery()))
    unread_count = await db.scalar(
        select(func.count()).where(
            Notification.user_id == current_user.id, Notification.read_at.is_(None)
        )
    )

    stmt = (
        base_stmt.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.scalars(stmt)).all()

    return NotificationListOut(
        items=[NotificationOut.model_validate(n) for n in rows],
        unread_count=unread_count or 0,
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationOut:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)

    return NotificationOut.model_validate(notification)


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int]:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read_at.is_(None))
        .values(read_at=func.now())
    )
    await db.commit()
    return {"updated": result.rowcount or 0}