import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.gamification import UserBadge
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
async def test_leaderboard_ranks_by_sightings_and_guess_points(gamification_app, gamification_client, db_session):
    zone = await _add_zone(db_session, "hall")
    bob = User(email="bob@example.com", display_name="Bob", guess_points=3)
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)

    db_session.add(Sighting(user_id=bob.id, zone_id=zone.id, image_path="cat.png"))
    await db_session.commit()

    await _login_as(gamification_app, db_session, User(email="alice@example.com", guess_points=0))

    response = gamification_client.get("/gamification/leaderboard")

    assert response.status_code == 200
    body = response.json()
    bob_entry = next(entry for entry in body if entry["user_id"] == bob.id)
    assert bob_entry["sighting_count"] == 1
    assert bob_entry["guess_points"] == 3
    assert bob_entry["score"] == 4
    assert body[0]["user_id"] == bob.id


@pytest.mark.asyncio
async def test_submit_guess_correct_awards_net_two_points(gamification_app, gamification_client, db_session):
    hall = await _add_zone(db_session, "hall")
    other = User(email="other@example.com")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    db_session.add(Sighting(user_id=other.id, zone_id=hall.id, image_path="cat.png"))
    await db_session.commit()

    alice = await _login_as(gamification_app, db_session, User(email="alice@example.com", guess_points=5))

    response = gamification_client.post("/gamification/guess", json={"zone_id": hall.id})

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["actual_zone_id"] == hall.id
    assert body["guess_points"] == 7
    await db_session.refresh(alice)
    assert alice.guess_points == 7


@pytest.mark.asyncio
async def test_submit_guess_wrong_costs_one_point(gamification_app, gamification_client, db_session):
    hall = await _add_zone(db_session, "hall")
    cafeteria = await _add_zone(db_session, "cafeteria")
    other = User(email="other@example.com")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    db_session.add(Sighting(user_id=other.id, zone_id=hall.id, image_path="cat.png"))
    await db_session.commit()

    await _login_as(gamification_app, db_session, User(email="alice@example.com", guess_points=5))

    response = gamification_client.post("/gamification/guess", json={"zone_id": cafeteria.id})

    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is False
    assert body["guess_points"] == 4


@pytest.mark.asyncio
async def test_submit_guess_with_no_points_returns_400(gamification_app, gamification_client, db_session):
    hall = await _add_zone(db_session, "hall")
    await _login_as(gamification_app, db_session, User(email="alice@example.com", guess_points=0))

    response = gamification_client.post("/gamification/guess", json={"zone_id": hall.id})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_guess_with_no_sightings_returns_400(gamification_app, gamification_client, db_session):
    hall = await _add_zone(db_session, "hall")
    await _login_as(gamification_app, db_session, User(email="alice@example.com", guess_points=5))

    response = gamification_client.post("/gamification/guess", json={"zone_id": hall.id})

    assert response.status_code == 400
