"""
Run: pytest tests/analytics/test_analytics_route.py -v
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.routers.analytics import router


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda c: Base.metadata.create_all(
                c, tables=[User.__table__, Zone.__table__, Sighting.__table__]
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession):
    alice = User(email="alice@example.com")
    bob = User(email="bob@example.com")
    zone_a = Zone(slug="campus-a", name="Campus A")
    zone_b = Zone(slug="campus-b", name="Campus B")
    db_session.add_all([alice, bob, zone_a, zone_b])
    await db_session.commit()
    for obj in (alice, bob, zone_a, zone_b):
        await db_session.refresh(obj)
    return {"alice": alice, "bob": bob, "zone_a": zone_a, "zone_b": zone_b}


def _sighting(user: User, zone: Zone, created_at: datetime, image: str = "cat.jpg") -> Sighting:
    s = Sighting(user_id=user.id, zone_id=zone.id, image_path=image)
    s.created_at = created_at
    return s


@pytest.fixture
def app(db_session, seeded):
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return seeded["alice"]

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_get_current_user
    return test_app


def test_analytics_summary_empty(app):
    resp = TestClient(app).get("/analytics/summary")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_sightings"] == 0
    assert body["window_days"] == 30
    assert body["zone_activity"] == []
    assert body["daily_trend"] == []
    assert body["top_reporters"] == []


@pytest.mark.asyncio
async def test_zone_activity_counts_sightings_per_zone(app, db_session, seeded):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], now),
            _sighting(seeded["bob"], seeded["zone_a"], now),
            _sighting(seeded["alice"], seeded["zone_b"], now),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary")
    zone_activity = {row["zone_name"]: row["count"] for row in resp.json()["zone_activity"]}

    assert zone_activity == {"Campus A": 2, "Campus B": 1}


@pytest.mark.asyncio
async def test_zone_activity_excludes_sightings_outside_window(app, db_session, seeded):
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=60)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], now),
            _sighting(seeded["alice"], seeded["zone_a"], old),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary?days=30")
    zone_activity = resp.json()["zone_activity"]

    assert len(zone_activity) == 1
    assert zone_activity[0]["count"] == 1


@pytest.mark.asyncio
async def test_daily_trend_groups_by_calendar_day(app, db_session, seeded):
    day1 = datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc)
    day1_later = datetime(2026, 8, 1, 18, 0, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], day1),
            _sighting(seeded["alice"], seeded["zone_a"], day1_later),
            _sighting(seeded["alice"], seeded["zone_a"], day2),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary?days=365")
    trend = {row["date"]: row["count"] for row in resp.json()["daily_trend"]}

    assert trend == {"2026-08-01": 2, "2026-08-02": 1}


@pytest.mark.asyncio
async def test_daily_trend_is_ordered_oldest_first(app, db_session, seeded):
    day1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], day2),
            _sighting(seeded["alice"], seeded["zone_a"], day1),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary?days=365")
    dates = [row["date"] for row in resp.json()["daily_trend"]]

    assert dates == ["2026-08-01", "2026-08-02"]


@pytest.mark.asyncio
async def test_top_reporters_is_all_time_not_windowed(app, db_session, seeded):
    # A sighting well outside the analytics window should still count
    # toward the leaderboard and the overall total - only zone_activity
    # and daily_trend are windowed, per the router's docstring.
    old = datetime.now(timezone.utc) - timedelta(days=400)
    db_session.add(_sighting(seeded["bob"], seeded["zone_a"], old))
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary?days=30")
    body = resp.json()

    assert body["total_sightings"] == 1
    assert body["zone_activity"] == []  # outside the 30-day window
    assert body["top_reporters"] == [
        {"user_id": seeded["bob"].id, "email": "bob@example.com", "count": 1}
    ]


@pytest.mark.asyncio
async def test_top_reporters_ordered_by_count_desc(app, db_session, seeded):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], now),
            _sighting(seeded["bob"], seeded["zone_a"], now),
            _sighting(seeded["bob"], seeded["zone_a"], now),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary")
    reporters = [row["email"] for row in resp.json()["top_reporters"]]

    assert reporters == ["bob@example.com", "alice@example.com"]


@pytest.mark.asyncio
async def test_top_reporters_respects_limit(app, db_session, seeded):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _sighting(seeded["alice"], seeded["zone_a"], now),
            _sighting(seeded["bob"], seeded["zone_a"], now),
        ]
    )
    await db_session.commit()

    resp = TestClient(app).get("/analytics/summary?reporter_limit=1")

    assert len(resp.json()["top_reporters"]) == 1


@pytest.mark.asyncio
async def test_days_query_param_controls_window_and_echoes_back(app, db_session, seeded):
    resp = TestClient(app).get("/analytics/summary?days=7")

    assert resp.json()["window_days"] == 7


@pytest.mark.asyncio
async def test_analytics_summary_requires_authentication(db_session):
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    resp = TestClient(test_app).get("/analytics/summary")

    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_analytics_rejects_invalid_query_parameters(app):
    client = TestClient(app)

    assert client.get("/analytics/summary?days=0").status_code == 422
    assert client.get("/analytics/summary?days=366").status_code == 422
    assert client.get("/analytics/summary?reporter_limit=0").status_code == 422
    assert client.get("/analytics/summary?reporter_limit=101").status_code == 422