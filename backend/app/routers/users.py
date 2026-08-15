from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.websocket_manager import manager
from app.models.friendship import Friendship, FriendshipStatus
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.auth import UserRead
from app.schemas.notification import NotificationCreate
from app.schemas.users import FriendEntry, FriendListRead, ProfileUpdate, PublicProfileRead, UserSearchResult
from app.services.notification_service import notify_user
from app.services.storage import save_upload

router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


@router.get("/me/friends", response_model=FriendListRead)
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FriendListRead:
    result = await db.execute(
        select(Friendship).where(
            or_(Friendship.requester_id == current_user.id, Friendship.addressee_id == current_user.id)
        )
    )
    rows = result.scalars().all()

    other_ids = {r.addressee_id if r.requester_id == current_user.id else r.requester_id for r in rows}
    users_result = await db.execute(select(User).where(User.id.in_(other_ids)))
    users_by_id = {u.id: u for u in users_result.scalars().all()}

    friends: list[FriendEntry] = []
    pending: list[FriendEntry] = []
    for row in rows:
        other_id = row.addressee_id if row.requester_id == current_user.id else row.requester_id
        other = users_by_id[other_id]
        entry = FriendEntry(
            friendship_id=row.id,
            id=other.id,
            display_name=other.display_name,
            avatar_url=other.avatar_url,
            online=manager.is_online(other.id),
        )
        if row.status == FriendshipStatus.ACCEPTED:
            friends.append(entry)
        elif row.addressee_id == current_user.id:
            pending.append(entry)

    return FriendListRead(friends=friends, pending_requests=pending)


@router.get("/search", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query(min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserSearchResult]:
    like = f"%{q}%"
    result = await db.execute(
        select(User)
        .where(
            User.id != current_user.id,
            or_(User.display_name.ilike(like), User.email.ilike(like)),
        )
        .order_by(User.display_name)
        .limit(20)
    )
    return [
        UserSearchResult(id=u.id, email=u.email, display_name=u.display_name, avatar_url=u.avatar_url)
        for u in result.scalars().all()
    ]


@router.post("/{user_id}/friend-request", status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if user_id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot friend yourself")

    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == user_id),
                and_(Friendship.requester_id == user_id, Friendship.addressee_id == current_user.id),
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Friendship already requested or exists")

    friendship = Friendship(requester_id=current_user.id, addressee_id=user_id)
    db.add(friendship)
    await db.commit()

    await notify_user(
        db,
        NotificationCreate(
            user_id=user_id,
            type=NotificationType.FRIEND_REQUEST,
            title=f"{current_user.display_name or current_user.email} sent you a friend request",
        ),
    )
    return {"status": "pending"}


@router.post("/me/friend-requests/{friendship_id}/accept", response_model=FriendEntry)
async def accept_friend_request(
    friendship_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FriendEntry:
    friendship = await db.get(Friendship, friendship_id)
    if friendship is None or friendship.addressee_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")

    friendship.status = FriendshipStatus.ACCEPTED
    await db.commit()

    other = await db.get(User, friendship.requester_id)
    return FriendEntry(
        friendship_id=friendship.id,
        id=other.id,
        display_name=other.display_name,
        avatar_url=other.avatar_url,
        online=manager.is_online(other.id),
    )


@router.delete("/{user_id}/friend", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Friendship).where(
            or_(
                and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == user_id),
                and_(Friendship.requester_id == user_id, Friendship.addressee_id == current_user.id),
            )
        )
    )
    friendship = result.scalar_one_or_none()
    if friendship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friendship not found")

    await db.delete(friendship)
    await db.commit()


@router.get("/{user_id}", response_model=PublicProfileRead)
async def get_public_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PublicProfileRead:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return PublicProfileRead(
        id=user.id,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        online=manager.is_online(user.id),
    )


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
