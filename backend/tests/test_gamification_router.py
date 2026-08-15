from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.gamification import Prediction, UserBadge
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.routers.gamification import router as gamification_router

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json(element, compiler, **kwargs):
    return "JSON"


@pytest.fixture
def gamification_app():
    return FastAPI()


@pytest.fixture
def gamification_client(gamification_app):
    gamification_app.include_router(gamification_router)
    return TestClient(gamification_app)


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


async def _login_as(gamification_app, db_session, user: User) -> User:
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_current_user():
        return user

    async def override_db():
        yield db_session

    gamification_app.dependency_overrides[get_current_user] = override_current_user
    gamification_app.dependency_overrides[get_db] = override_db
    return user


async def _add_zone(db_session, slug: str) -> Zone:
    zone = Zone(slug=slug, name=slug.title())
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


@pytest.mark.asyncio
async def test_list_achievements_returns_earned_badges(gamification_app, gamification_client, db_session):
    alice = await _login_as(gamification_app, db_session, User(email="alice@example.com"))
    db_session.add(UserBadge(user_id=alice.id, badge_code="first_sighting"))
    await db_session.commit()

    response = gamification_client.get("/gamification/achievements")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "first_sighting"
    assert body[0]["name"] == "First Sighting"


@pytest.mark.asyncio
async def test_leaderboard_ranks_by_sightings_and_correct_predictions(
    gamification_app, gamification_client, db_session
):
    zone = await _add_zone(db_session, "hall")
    bob = User(email="bob@example.com", display_name="Bob")
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)

    db_session.add(Sighting(user_id=bob.id, zone_id=zone.id, image_path="cat.png"))
    db_session.add(
        Prediction(user_id=bob.id, zone_id=zone.id, target_date=date(2026, 1, 1), is_correct=True)
    )
    await db_session.commit()

    await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    response = gamification_client.get("/gamification/leaderboard")

    assert response.status_code == 200
    body = response.json()
    bob_entry = next(entry for entry in body if entry["user_id"] == bob.id)
    assert bob_entry["sighting_count"] == 1
    assert bob_entry["correct_predictions"] == 1
    assert bob_entry["score"] == 11
    assert body[0]["user_id"] == bob.id


@pytest.mark.asyncio
async def test_submit_prediction_creates_row_for_tomorrow(gamification_app, gamification_client, db_session):
    zone = await _add_zone(db_session, "hall")
    await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    response = gamification_client.post("/gamification/predictions", json={"zone_id": zone.id})

    assert response.status_code == 201
    body = response.json()
    assert body["zone_id"] == zone.id
    assert body["target_date"] == str(date.today() + timedelta(days=1))
    assert body["is_correct"] is None


@pytest.mark.asyncio
async def test_submit_duplicate_prediction_for_same_day_returns_409(
    gamification_app, gamification_client, db_session
):
    zone = await _add_zone(db_session, "hall")
    await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    first = gamification_client.post("/gamification/predictions", json={"zone_id": zone.id})
    second = gamification_client.post("/gamification/predictions", json={"zone_id": zone.id})

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_submit_prediction_for_missing_zone_returns_404(gamification_app, gamification_client, db_session):
    await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    response = gamification_client.post("/gamification/predictions", json={"zone_id": 999})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_my_predictions_settles_past_prediction_against_winning_zone(
    gamification_app, gamification_client, db_session
):
    hall = await _add_zone(db_session, "hall")
    cafeteria = await _add_zone(db_session, "cafeteria")
    alice = await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    yesterday = date.today() - timedelta(days=1)
    db_session.add(Prediction(user_id=alice.id, zone_id=hall.id, target_date=yesterday))

    start = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
    sighting = Sighting(user_id=alice.id, zone_id=hall.id, image_path="cat.png")
    db_session.add(sighting)
    db_session.add(Sighting(user_id=alice.id, zone_id=cafeteria.id, image_path="cat2.png"))
    await db_session.commit()
    await db_session.refresh(sighting)
    sighting.created_at = start
    await db_session.commit()

    response = gamification_client.get("/gamification/predictions/me")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["is_correct"] is True


@pytest.mark.asyncio
async def test_my_predictions_leaves_unsettled_when_no_sightings_that_day(
    gamification_app, gamification_client, db_session
):
    hall = await _add_zone(db_session, "hall")
    alice = await _login_as(gamification_app, db_session, User(email="alice@example.com"))

    yesterday = date.today() - timedelta(days=1)
    db_session.add(Prediction(user_id=alice.id, zone_id=hall.id, target_date=yesterday))
    await db_session.commit()

    response = gamification_client.get("/gamification/predictions/me")

    assert response.status_code == 200
    assert response.json()[0]["is_correct"] is None
