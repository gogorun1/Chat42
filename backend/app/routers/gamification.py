from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.gamification import Prediction, UserBadge
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.schemas.gamification import BadgeRead, LeaderboardEntry, PredictionCreate, PredictionRead
from app.services.gamification_service import BADGE_RULES, settle_pending_predictions

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
    await settle_pending_predictions(db)

    sighting_counts = dict(
        (await db.execute(select(Sighting.user_id, func.count(Sighting.id)).group_by(Sighting.user_id))).all()
    )
    correct_counts = dict(
        (
            await db.execute(
                select(Prediction.user_id, func.count(Prediction.id))
                .where(Prediction.is_correct.is_(True))
                .group_by(Prediction.user_id)
            )
        ).all()
    )

    users = (await db.execute(select(User))).scalars().all()
    entries = [
        LeaderboardEntry(
            user_id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            sighting_count=sighting_counts.get(user.id, 0),
            correct_predictions=correct_counts.get(user.id, 0),
            score=sighting_counts.get(user.id, 0) + correct_counts.get(user.id, 0) * 10,
        )
        for user in users
    ]
    entries.sort(key=lambda entry: entry.score, reverse=True)
    return entries[offset : offset + limit]


@router.post("/predictions", response_model=PredictionRead, status_code=status.HTTP_201_CREATED)
async def submit_prediction(
    payload: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PredictionRead:
    zone = await db.get(Zone, payload.zone_id)
    if zone is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zone not found")

    target_date = date.today() + timedelta(days=1)
    existing = await db.execute(
        select(Prediction).where(Prediction.user_id == current_user.id, Prediction.target_date == target_date)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already submitted a prediction for tomorrow")

    prediction = Prediction(user_id=current_user.id, zone_id=payload.zone_id, target_date=target_date)
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    return PredictionRead.model_validate(prediction)


@router.get("/predictions/me", response_model=list[PredictionRead])
async def my_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionRead]:
    await settle_pending_predictions(db)

    result = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == current_user.id)
        .order_by(Prediction.target_date.desc())
    )
    return [PredictionRead.model_validate(prediction) for prediction in result.scalars().all()]
