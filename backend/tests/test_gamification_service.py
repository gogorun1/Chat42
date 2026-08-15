import pytest
import pytest_asyncio
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.services.gamification_service import check_and_award_badges

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json(element, compiler, **kwargs):
    return "JSON"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _add_zone(db_session, slug: str) -> Zone:
    zone = Zone(slug=slug, name=slug.title())
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


async def _add_user(db_session) -> User:
    user = User(email="alice@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _add_sighting(db_session, user: User, zone: Zone, created_at=None) -> Sighting:
    sighting = Sighting(user_id=user.id, zone_id=zone.id, image_path="cat.png")
    db_session.add(sighting)
    await db_session.commit()
    await db_session.refresh(sighting)
    if created_at is not None:
        sighting.created_at = created_at
        await db_session.commit()
    return sighting


@pytest.mark.asyncio
async def test_first_sighting_awards_badge(db_session):
    user = await _add_user(db_session)
    zone = await _add_zone(db_session, "hall")
    await _add_zone(db_session, "cafeteria")  # unvisited, keeps zone_explorer from firing
    await _add_sighting(db_session, user, zone)

    new_codes = await check_and_award_badges(db_session, user)

    assert new_codes == ["first_sighting"]


@pytest.mark.asyncio
async def test_badge_not_awarded_twice(db_session):
    user = await _add_user(db_session)
    zone = await _add_zone(db_session, "hall")
    await _add_sighting(db_session, user, zone)

    await check_and_award_badges(db_session, user)
    second_call = await check_and_award_badges(db_session, user)

    assert second_call == []


@pytest.mark.asyncio
async def test_five_sightings_awards_badge(db_session):
    user = await _add_user(db_session)
    zone = await _add_zone(db_session, "hall")
    await _add_zone(db_session, "cafeteria")  # unvisited, keeps zone_explorer from firing
    for _ in range(5):
        await _add_sighting(db_session, user, zone)

    new_codes = await check_and_award_badges(db_session, user)

    assert set(new_codes) == {"first_sighting", "five_sightings"}


@pytest.mark.asyncio
async def test_zone_explorer_requires_every_zone(db_session):
    user = await _add_user(db_session)
    hall = await _add_zone(db_session, "hall")
    cafeteria = await _add_zone(db_session, "cafeteria")

    await _add_sighting(db_session, user, hall)
    new_codes = await check_and_award_badges(db_session, user)
    assert "zone_explorer" not in new_codes

    await _add_sighting(db_session, user, cafeteria)
    new_codes = await check_and_award_badges(db_session, user)
    assert "zone_explorer" in new_codes


@pytest.mark.asyncio
async def test_week_streak_requires_seven_consecutive_days(db_session):
    from datetime import datetime, timedelta, timezone

    user = await _add_user(db_session)
    zone = await _add_zone(db_session, "hall")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for day_offset in range(7):
        await _add_sighting(db_session, user, zone, created_at=start + timedelta(days=day_offset))

    new_codes = await check_and_award_badges(db_session, user)

    assert "week_streak" in new_codes


@pytest.mark.asyncio
async def test_week_streak_not_awarded_with_a_gap(db_session):
    from datetime import datetime, timedelta, timezone

    user = await _add_user(db_session)
    zone = await _add_zone(db_session, "hall")
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for day_offset in [0, 1, 2, 3, 5, 6, 7]:
        await _add_sighting(db_session, user, zone, created_at=start + timedelta(days=day_offset))

    new_codes = await check_and_award_badges(db_session, user)

    assert "week_streak" not in new_codes
