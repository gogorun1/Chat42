import io

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.friendship import Friendship, FriendshipStatus
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.routers.users import router as users_router

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json(element, compiler, **kwargs):
    return "JSON"


@pytest.fixture
def users_app():
    return FastAPI()


@pytest.fixture
def users_client(users_app):
    users_app.include_router(users_router)
    return TestClient(users_app)


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


async def _login_as(users_app, db_session, user: User) -> User:
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_current_user():
        return user

    async def override_db():
        yield db_session

    users_app.dependency_overrides[get_current_user] = override_current_user
    users_app.dependency_overrides[get_db] = override_db
    return user


@pytest.mark.asyncio
async def test_update_profile_sets_display_name(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.patch("/users/me", json={"display_name": "Alice"})

    assert response.status_code == 200
    assert response.json()["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_update_profile_rejects_empty_display_name(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.patch("/users/me", json={"display_name": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_avatar_sets_avatar_url(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post(
        "/users/me/avatar",
        files={"avatar": ("cat.png", io.BytesIO(b"fake-image-bytes"), "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"].startswith("/uploads/")


@pytest.mark.asyncio
async def test_upload_avatar_rejects_bad_content_type(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post(
        "/users/me/avatar",
        files={"avatar": ("cat.txt", io.BytesIO(b"not-an-image"), "text/plain")},
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_get_public_profile_returns_offline_by_default(users_app, users_client, db_session):
    target = User(email="bob@example.com", display_name="Bob")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.get(f"/users/{target.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Bob"
    assert body["online"] is False


@pytest.mark.asyncio
async def test_get_public_profile_missing_user_returns_404(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.get("/users/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_users_matches_display_name_case_insensitively(users_app, users_client, db_session):
    db_session.add_all(
        [
            User(email="bob@example.com", display_name="Bob Builder"),
            User(email="carol@example.com", display_name="Carol"),
        ]
    )
    await db_session.commit()

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.get("/users/search", params={"q": "bob"})

    assert response.status_code == 200
    results = response.json()
    assert [r["display_name"] for r in results] == ["Bob Builder"]
    assert results[0]["email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_search_users_matches_email(users_app, users_client, db_session):
    db_session.add(User(email="findme@example.com", display_name=None))
    await db_session.commit()

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.get("/users/search", params={"q": "findme"})

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_search_users_excludes_self(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com", display_name="Alice"))

    response = users_client.get("/users/search", params={"q": "alice"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_users_requires_query(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.get("/users/search")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_send_friend_request_creates_pending_row_and_notification(
    users_app, users_client, db_session
):
    target = User(email="bob@example.com")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post(f"/users/{target.id}/friend-request")

    assert response.status_code == 201

    friendships = (await db_session.execute(select(Friendship))).scalars().all()
    assert len(friendships) == 1
    assert friendships[0].status == FriendshipStatus.PENDING

    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.FRIEND_REQUEST
    assert notifications[0].user_id == target.id


@pytest.mark.asyncio
async def test_send_friend_request_to_self_returns_400(users_app, users_client, db_session):
    alice = await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post(f"/users/{alice.id}/friend-request")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_send_friend_request_to_missing_user_returns_404(users_app, users_client, db_session):
    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post("/users/999/friend-request")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_friend_request_returns_409(users_app, users_client, db_session):
    target = User(email="bob@example.com")
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    first = users_client.post(f"/users/{target.id}/friend-request")
    second = users_client.post(f"/users/{target.id}/friend-request")

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_accept_friend_request_marks_accepted_and_shows_in_friends_list(
    users_app, users_client, db_session
):
    bob = User(email="bob@example.com")
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)

    alice = await _login_as(users_app, db_session, User(email="alice@example.com"))

    friendship = Friendship(requester_id=bob.id, addressee_id=alice.id)
    db_session.add(friendship)
    await db_session.commit()
    await db_session.refresh(friendship)

    response = users_client.post(f"/users/me/friend-requests/{friendship.id}/accept")
    assert response.status_code == 200

    friends_response = users_client.get("/users/me/friends")
    assert friends_response.status_code == 200
    body = friends_response.json()
    assert len(body["friends"]) == 1
    assert body["friends"][0]["id"] == bob.id
    assert body["pending_requests"] == []


@pytest.mark.asyncio
async def test_accept_friend_request_not_addressed_to_me_returns_404(
    users_app, users_client, db_session
):
    bob = User(email="bob@example.com")
    carol = User(email="carol@example.com")
    db_session.add_all([bob, carol])
    await db_session.commit()
    await db_session.refresh(bob)
    await db_session.refresh(carol)

    friendship = Friendship(requester_id=bob.id, addressee_id=carol.id)
    db_session.add(friendship)
    await db_session.commit()
    await db_session.refresh(friendship)

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.post(f"/users/me/friend-requests/{friendship.id}/accept")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_friend_deletes_relationship(users_app, users_client, db_session):
    bob = User(email="bob@example.com")
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)

    alice = await _login_as(users_app, db_session, User(email="alice@example.com"))
    friendship = Friendship(
        requester_id=alice.id, addressee_id=bob.id, status=FriendshipStatus.ACCEPTED
    )
    db_session.add(friendship)
    await db_session.commit()

    response = users_client.delete(f"/users/{bob.id}/friend")

    assert response.status_code == 204
    remaining = (await db_session.execute(select(Friendship))).scalars().all()
    assert remaining == []


@pytest.mark.asyncio
async def test_remove_nonexistent_friend_returns_404(users_app, users_client, db_session):
    bob = User(email="bob@example.com")
    db_session.add(bob)
    await db_session.commit()
    await db_session.refresh(bob)

    await _login_as(users_app, db_session, User(email="alice@example.com"))

    response = users_client.delete(f"/users/{bob.id}/friend")

    assert response.status_code == 404
