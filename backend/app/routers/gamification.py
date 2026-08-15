from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.gamification import UserBadge
from app.models.sighting import Sighting
from app.models.user import User
from app.schemas.gamification import BadgeRead, GuessCreate, GuessResult, LeaderboardEntry
from app.services.gamification_service import BADGE_RULES

router = APIRouter(prefix="/gamification", tags=["gamification"])

_BADGE_INFO = {code: (name, description) for code, name, description in BADGE_RULES}


@router.get("/achievements", response_model=list[BadgeRead])
async def list_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BadgeRead]:
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == current_user.id).order_by(UserBadge.awarded_at)
    )
    badges = result.scalars().all()
    return [
        BadgeRead(
            code=badge.badge_code,
            name=_BADGE_INFO.get(badge.badge_code, (badge.badge_code, ""))[0],
            description=_BADGE_INFO.get(badge.badge_code, (badge.badge_code, ""))[1],
            awarded_at=badge.awarded_at,
        )
        for badge in badges
    ]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LeaderboardEntry]:
    sighting_counts = dict(
        (await db.execute(select(Sighting.user_id, func.count(Sighting.id)).group_by(Sighting.user_id))).all()
    )

    users = (await db.execute(select(User))).scalars().all()
    entries = [
        LeaderboardEntry(
            user_id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            sighting_count=sighting_counts.get(user.id, 0),
            guess_points=user.guess_points,
            score=sighting_counts.get(user.id, 0) + user.guess_points,
        )
        for user in users
    ]
    entries.sort(key=lambda entry: entry.score, reverse=True)
    return entries[offset : offset + limit]


@router.post("/guess", response_model=GuessResult)
async def submit_guess(
    payload: GuessCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuessResult:
    if current_user.guess_points < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not enough points")

    latest = (
        await db.execute(select(Sighting).order_by(Sighting.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    if latest is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No sightings yet to guess against")

    correct = payload.zone_id == latest.zone_id
    current_user.guess_points -= 1
    if correct:
        current_user.guess_points += 3
    await db.commit()
    await db.refresh(current_user)

    return GuessResult(correct=correct, guess_points=current_user.guess_points, actual_zone_id=latest.zone_id)
