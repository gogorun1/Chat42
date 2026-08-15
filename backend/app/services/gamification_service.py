"""
Badge rules are static and code-defined (not a DB table) — this project has
no need for admin-configurable badges, and a table would just be an extra
migration/CRUD surface for no benefit. `BADGE_RULES` is the single source of
truth for what a badge means; `UserBadge` rows only record who earned which
`badge_code`.

Call `check_and_award_badges()` after a sighting is successfully persisted
(see app/routers/sightings.py::create_sighting, right after `await
db.commit()`) so badge state never drifts from the sightings it's derived
from.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Prediction, UserBadge
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone

BADGE_RULES: list[tuple[str, str, str]] = [
    ("first_sighting", "First Sighting", "Log your first cat sighting."),
    ("five_sightings", "Regular Spotter", "Log 5 cat sightings."),
    ("ten_sightings", "Dedicated Spotter", "Log 10 cat sightings."),
    ("fifty_sightings", "Cat Whisperer", "Log 50 cat sightings."),
    ("zone_explorer", "Zone Explorer", "Spot a cat in every zone on campus."),
    ("week_streak", "Seven Day Streak", "Log a sighting on 7 different days in a row."),
]


def _has_week_streak(days: set[date]) -> bool:
    if len(days) < 7:
        return False
    ordered = sorted(days)
    streak = 1
    for previous, current in zip(ordered, ordered[1:]):
        streak = streak + 1 if (current - previous).days == 1 else 1
        if streak >= 7:
            return True
    return False


async def check_and_award_badges(db: AsyncSession, user: User) -> list[str]:
    already_awarded = set(
        (await db.execute(select(UserBadge.badge_code).where(UserBadge.user_id == user.id)))
        .scalars()
        .all()
    )

    rows = (
        (await db.execute(select(Sighting.zone_id, Sighting.created_at).where(Sighting.user_id == user.id)))
        .all()
    )
    total = len(rows)
    distinct_zones = {zone_id for zone_id, _ in rows}
    total_zones = (await db.execute(select(func.count()).select_from(Zone))).scalar_one()

    earned: set[str] = set()
    if total >= 1:
        earned.add("first_sighting")
    if total >= 5:
        earned.add("five_sightings")
    if total >= 10:
        earned.add("ten_sightings")
    if total >= 50:
        earned.add("fifty_sightings")
    if total_zones > 0 and len(distinct_zones) >= total_zones:
        earned.add("zone_explorer")
    if _has_week_streak({created_at.date() for _, created_at in rows}):
        earned.add("week_streak")

    new_codes = sorted(earned - already_awarded)
    for code in new_codes:
        db.add(UserBadge(user_id=user.id, badge_code=code))
    if new_codes:
        await db.commit()

    return new_codes


async def settle_pending_predictions(db: AsyncSession) -> None:
    """
    Lazy settlement: there's no cron/scheduler in the deploy stack, so instead
    of resolving "yesterday's" guesses on a timer, we resolve them the next
    time anyone asks for predictions or the leaderboard. A day's winner is
    whichever zone had the most sightings on `target_date` (UTC calendar
    day); ties count as correct for every tied zone. A day with zero
    sightings is left unresolved (`is_correct` stays None) rather than
    penalizing everyone who guessed.
    """
    today = date.today()
    pending = (
        (
            await db.execute(
                select(Prediction).where(Prediction.target_date < today, Prediction.is_correct.is_(None))
            )
        )
        .scalars()
        .all()
    )
    if not pending:
        return

    for target_date in {p.target_date for p in pending}:
        start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        counts = (
            await db.execute(
                select(Sighting.zone_id, func.count(Sighting.id))
                .where(Sighting.created_at >= start, Sighting.created_at < end)
                .group_by(Sighting.zone_id)
            )
        ).all()
        if not counts:
            continue

        max_count = max(count for _, count in counts)
        winning_zones = {zone_id for zone_id, count in counts if count == max_count}

        for prediction in pending:
            if prediction.target_date == target_date:
                prediction.is_correct = prediction.zone_id in winning_zones

    await db.commit()
