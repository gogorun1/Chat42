"""
Run: pytest tests/search/test_search_route.py -v
"""
from __future__ import annotations

from datetime import datetime

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
from app.routers.search import router


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
    """Common fixture data most tests build on: two users, two zones."""
    alice = User(email="alice@example.com")
    bob = User(email="bob@example.com")
    zone_a = Zone(slug="campus-a", name="Campus A")
    zone_b = Zone(slug="campus-b", name="Campus B")
    db_session.add_all([alice, bob, zone_a, zone_b])
    await db_session.commit()
    for obj in (alice, bob, zone_a, zone_b):
        await db_session.refresh(obj)
    return {"alice": alice, "bob": bob, "zone_a": zone_a, "zone_b": zone_b}


def _sighting(user: User, zone: Zone, image: str = "cat.jpg", created_at: datetime | None = None) -> Sighting:
    s = Sighting(user_id=user.id, zone_id=zone.id, image_path=image)
    if created_at is not None:
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


def test_search_sightings_empty(app):
    resp = TestClient(app).get("/search/sightings")

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 20}


@pytest.mark.asyncio
async def test_search_sightings_returns_sightings_from_all_users(app, db_session, seeded):
    a = _sighting(seeded["alice"], seeded["zone_a"], "alice-cat.jpg")
    b = _sighting(seeded["bob"], seeded["zone_b"], "bob-cat.jpg")
    db_session.add_all([a, b])
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings")
    body = resp.json()

    assert body["total"] == 2
    assert {item["id"] for item in body["items"]} == {a.id, b.id}


@pytest.mark.asyncio
async def test_search_sightings_filters_by_zone(app, db_session, seeded):
    a = _sighting(seeded["alice"], seeded["zone_a"], "cat-a.jpg")
    b = _sighting(seeded["bob"], seeded["zone_b"], "cat-b.jpg")
    db_session.add_all([a, b])
    await db_session.commit()

    resp = TestClient(app).get(f"/search/sightings?zone_id={seeded['zone_a'].id}")
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == a.id
    assert body["items"][0]["zone_name"] == "Campus A"


@pytest.mark.asyncio
async def test_search_sightings_filters_by_user(app, db_session, seeded):
    a = _sighting(seeded["alice"], seeded["zone_a"], "alice-cat.jpg")
    b = _sighting(seeded["bob"], seeded["zone_a"], "bob-cat.jpg")
    db_session.add_all([a, b])
    await db_session.commit()

    resp = TestClient(app).get(f"/search/sightings?user_id={seeded['bob'].id}")
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == b.id
    assert body["items"][0]["reporter_id"] == seeded["bob"].id
    assert body["items"][0]["reporter_email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_search_sightings_filters_by_date(app, db_session, seeded):
    old = _sighting(seeded["alice"], seeded["zone_a"], "old-cat.jpg", datetime(2024, 1, 1, 12, 0))
    new = _sighting(seeded["alice"], seeded["zone_a"], "new-cat.jpg", datetime(2025, 1, 1, 12, 0))
    db_session.add_all([old, new])
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings?date_from=2024-06-01T00:00:00")
    body = resp.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == new.id


@pytest.mark.asyncio
async def test_search_sightings_defaults_to_newest_first(app, db_session, seeded):
    older = _sighting(seeded["alice"], seeded["zone_a"], "older.jpg", datetime(2024, 1, 1, 12, 0))
    newer = _sighting(seeded["alice"], seeded["zone_a"], "newer.jpg", datetime(2025, 1, 1, 12, 0))
    db_session.add_all([older, newer])
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings")

    assert [item["id"] for item in resp.json()["items"]] == [newer.id, older.id]


@pytest.mark.asyncio
async def test_search_sightings_sorts_by_created_at_ascending(app, db_session, seeded):
    older = _sighting(seeded["alice"], seeded["zone_a"], "older.jpg", datetime(2024, 1, 1, 12, 0))
    newer = _sighting(seeded["alice"], seeded["zone_a"], "newer.jpg", datetime(2025, 1, 1, 12, 0))
    db_session.add_all([older, newer])
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings?sort_by=created_at&sort_order=asc")

    assert [item["id"] for item in resp.json()["items"]] == [older.id, newer.id]


@pytest.mark.asyncio
async def test_search_sightings_sorts_by_zone(app, db_session, seeded):
    b = _sighting(seeded["alice"], seeded["zone_b"], "cat-b.jpg")
    a = _sighting(seeded["alice"], seeded["zone_a"], "cat-a.jpg")
    db_session.add_all([b, a])
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings?sort_by=zone&sort_order=asc")

    assert [item["zone_name"] for item in resp.json()["items"]] == ["Campus A", "Campus B"]


@pytest.mark.asyncio
async def test_search_sightings_pagination(app, db_session, seeded):
    for i in range(5):
        db_session.add(_sighting(seeded["alice"], seeded["zone_a"], f"cat-{i}.jpg", datetime(2024, 1, i + 1, 12, 0)))
    await db_session.commit()

    resp = TestClient(app).get("/search/sightings?page=2&page_size=2")
    body = resp.json()

    assert body["total"] == 5
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_search_sightings_requires_authentication(db_session):
    test_app = FastAPI()
    test_app.include_router(router)

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    resp = TestClient(test_app).get("/search/sightings")

    assert resp.status_code == 401