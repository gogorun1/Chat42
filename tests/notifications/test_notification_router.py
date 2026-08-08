"""
Run: pytest tests/notifications/test_notifications_router.py -v

"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.routers.notifications import router


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json_on_sqlite(element, compiler, **kw):
    return "JSON"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[User.__table__, Notification.__table__]
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_users(db_session: AsyncSession):
    alice = User(email="alice@example.com")
    bob = User(email="bob@example.com")
    db_session.add_all([alice, bob])
    await db_session.commit()
    return {"alice": alice, "bob": bob}


@pytest.fixture
def app(db_session, seeded_users):
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api")

    async def _override_get_db():
        yield db_session

    # Route through get_current_user's real dependency, but swap in whichever
    # seeded user the test wants logged in — override changes per-test below.
    test_app.dependency_overrides[get_db] = _override_get_db
    test_app.state.current_user = seeded_users["alice"]  # default; tests can reassign

    async def _override_get_current_user():
        return test_app.state.current_user

    test_app.dependency_overrides[get_current_user] = _override_get_current_user
    return test_app


def _make_notification(user_id: int, title: str, read: bool = False) -> Notification:
    n = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=NotificationType.SYSTEM,
        title=title,
        data={},
    )
    n.created_at = datetime.now(timezone.utc)
    if read:
        n.read_at = datetime.now(timezone.utc)
    return n


@pytest.mark.asyncio
async def test_list_notifications_empty_by_default(app, db_session, seeded_users):
    client = TestClient(app)
    resp = client.get("/api/notifications")

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["unread_count"] == 0


@pytest.mark.asyncio
async def test_list_notifications_returns_only_current_users_rows(app, db_session, seeded_users):
    db_session.add(_make_notification(seeded_users["alice"].id, "For Alice"))
    db_session.add(_make_notification(seeded_users["bob"].id, "For Bob"))
    await db_session.commit()

    client = TestClient(app)  # app.state.current_user defaults to alice
    resp = client.get("/api/notifications")

    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "For Alice"


@pytest.mark.asyncio
async def test_unread_count_ignores_already_read_notifications(app, db_session, seeded_users):
    db_session.add(_make_notification(seeded_users["alice"].id, "Unread one"))
    db_session.add(_make_notification(seeded_users["alice"].id, "Already read", read=True))
    await db_session.commit()

    client = TestClient(app)
    resp = client.get("/api/notifications")

    body = resp.json()
    assert body["total"] == 2
    assert body["unread_count"] == 1


@pytest.mark.asyncio
async def test_unread_only_filter(app, db_session, seeded_users):
    db_session.add(_make_notification(seeded_users["alice"].id, "Unread one"))
    db_session.add(_make_notification(seeded_users["alice"].id, "Already read", read=True))
    await db_session.commit()

    client = TestClient(app)
    resp = client.get("/api/notifications?unread_only=true")

    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Unread one"


@pytest.mark.asyncio
async def test_pagination(app, db_session, seeded_users):
    for i in range(5):
        db_session.add(_make_notification(seeded_users["alice"].id, f"Notif {i}"))
    await db_session.commit()

    client = TestClient(app)
    resp = client.get("/api/notifications?page=1&page_size=2")
    body = resp.json()

    assert body["total"] == 5
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_mark_read_flips_is_read_and_persists(app, db_session, seeded_users):
    notification = _make_notification(seeded_users["alice"].id, "Mark me")
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    client = TestClient(app)
    resp = client.post(f"/api/notifications/{notification.id}/read")

    assert resp.status_code == 200
    assert resp.json()["is_read"] is True

    # Confirm it actually persisted, not just returned in the response.
    list_resp = client.get("/api/notifications")
    assert list_resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_read_404s_for_another_users_notification(app, db_session, seeded_users):
    bobs_notification = _make_notification(seeded_users["bob"].id, "Not yours")
    db_session.add(bobs_notification)
    await db_session.commit()
    await db_session.refresh(bobs_notification)

    client = TestClient(app)  # logged in as alice (the app fixture's default)
    resp = client.post(f"/api/notifications/{bobs_notification.id}/read")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_read_404s_for_nonexistent_id(app, db_session):
    client = TestClient(app)
    resp = client.post(f"/api/notifications/{uuid.uuid4()}/read")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read_only_touches_current_users_unread(app, db_session, seeded_users):
    db_session.add(_make_notification(seeded_users["alice"].id, "Alice unread 1"))
    db_session.add(_make_notification(seeded_users["alice"].id, "Alice unread 2"))
    db_session.add(_make_notification(seeded_users["bob"].id, "Bob unread"))
    await db_session.commit()

    client = TestClient(app)  # alice
    resp = client.post("/api/notifications/read-all")

    assert resp.status_code == 200
    assert resp.json()["updated"] == 2

    # Bob's notification must be untouched.
    app.state.current_user = seeded_users["bob"]
    bob_resp = client.get("/api/notifications")
    assert bob_resp.json()["unread_count"] == 1

@pytest.mark.asyncio
async def test_notifications_are_returned_newest_first(
    app,
    db_session,
    seeded_users,
):
    old = _make_notification(
        seeded_users["alice"].id,
        "Old notification",
    )
    new = _make_notification(
        seeded_users["alice"].id,
        "New notification",
    )

    old.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    new.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    db_session.add_all([old, new])
    await db_session.commit()

    client = TestClient(app)

    response = client.get("/api/notifications")

    titles = [
        item["title"]
        for item in response.json()["items"]
    ]

    assert titles == [
        "New notification",
        "Old notification",
    ]