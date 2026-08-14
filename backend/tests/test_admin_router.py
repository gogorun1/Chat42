import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.models.sighting import Sighting
from app.models.user import User, UserRole
from app.models.zone import Zone
from app.routers.admin import router as admin_router

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json(element, compiler, **kwargs):
    return "JSON"


@pytest.fixture
def admin_app():
    return FastAPI()


@pytest.fixture
def admin_client(admin_app):
    admin_app.include_router(admin_router)
    return TestClient(admin_app)


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


async def _login_as(admin_app, db_session, role: UserRole) -> User:
    user = User(email=f"{role.value}@example.com", role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_current_user():
        return user

    async def override_db():
        yield db_session

    admin_app.dependency_overrides[get_current_user] = override_current_user
    admin_app.dependency_overrides[get_db] = override_db
    return user


@pytest.mark.asyncio
async def test_plain_user_cannot_create_zone(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.USER)

    response = admin_client.post("/admin/zones", json={"slug": "library", "name": "Library"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_moderator_can_create_zone(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.post("/admin/zones", json={"slug": "library", "name": "Library"})

    assert response.status_code == 201
    assert response.json()["slug"] == "library"


@pytest.mark.asyncio
async def test_create_zone_rejects_duplicate_slug(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.MODERATOR)
    db_session.add(Zone(slug="library", name="Library"))
    await db_session.commit()

    response = admin_client.post("/admin/zones", json={"slug": "library", "name": "Library 2"})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_admin_can_update_zone(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.ADMIN)
    zone = Zone(slug="library", name="Library")
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)

    response = admin_client.patch(f"/admin/zones/{zone.id}", json={"name": "Main Library"})

    assert response.status_code == 200
    assert response.json()["name"] == "Main Library"


@pytest.mark.asyncio
async def test_update_missing_zone_returns_404(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.patch("/admin/zones/999", json={"name": "Ghost"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_moderator_can_delete_empty_zone(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.MODERATOR)
    zone = Zone(slug="library", name="Library")
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)

    response = admin_client.delete(f"/admin/zones/{zone.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_zone_with_sightings_conflicts(admin_app, admin_client, db_session):
    reporter = User(email="reporter@example.com")
    zone = Zone(slug="library", name="Library")
    db_session.add_all([reporter, zone])
    await db_session.commit()
    await db_session.refresh(reporter)
    await db_session.refresh(zone)

    db_session.add(Sighting(user_id=reporter.id, zone_id=zone.id, image_path="cat.png"))
    await db_session.commit()

    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.delete(f"/admin/zones/{zone.id}")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_moderator_can_reassign_sighting_zone(admin_app, admin_client, db_session):
    reporter = User(email="reporter@example.com")
    wrong_zone = Zone(slug="library", name="Library")
    right_zone = Zone(slug="canteen", name="Canteen")
    db_session.add_all([reporter, wrong_zone, right_zone])
    await db_session.commit()
    await db_session.refresh(reporter)
    await db_session.refresh(wrong_zone)
    await db_session.refresh(right_zone)

    sighting = Sighting(user_id=reporter.id, zone_id=wrong_zone.id, image_path="cat.png")
    db_session.add(sighting)
    await db_session.commit()
    await db_session.refresh(sighting)

    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.patch(
        f"/admin/sightings/{sighting.id}", json={"zone_id": right_zone.id}
    )

    assert response.status_code == 200
    assert response.json()["zone_id"] == right_zone.id
    assert response.json()["zone"]["slug"] == "canteen"


@pytest.mark.asyncio
async def test_reassign_missing_sighting_returns_404(admin_app, admin_client, db_session):
    zone = Zone(slug="library", name="Library")
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)

    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.patch("/admin/sightings/999", json={"zone_id": zone.id})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reassign_sighting_to_missing_zone_returns_404(admin_app, admin_client, db_session):
    reporter = User(email="reporter@example.com")
    zone = Zone(slug="library", name="Library")
    db_session.add_all([reporter, zone])
    await db_session.commit()
    await db_session.refresh(reporter)
    await db_session.refresh(zone)

    sighting = Sighting(user_id=reporter.id, zone_id=zone.id, image_path="cat.png")
    db_session.add(sighting)
    await db_session.commit()
    await db_session.refresh(sighting)

    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.patch(f"/admin/sightings/{sighting.id}", json={"zone_id": 999})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_plain_user_cannot_delete_sighting(admin_app, admin_client, db_session):
    reporter = User(email="reporter@example.com")
    zone = Zone(slug="library", name="Library")
    db_session.add_all([reporter, zone])
    await db_session.commit()
    await db_session.refresh(reporter)
    await db_session.refresh(zone)

    sighting = Sighting(user_id=reporter.id, zone_id=zone.id, image_path="cat.png")
    db_session.add(sighting)
    await db_session.commit()
    await db_session.refresh(sighting)

    await _login_as(admin_app, db_session, UserRole.USER)

    response = admin_client.delete(f"/admin/sightings/{sighting.id}")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_delete_sighting(admin_app, admin_client, db_session):
    reporter = User(email="reporter@example.com")
    zone = Zone(slug="library", name="Library")
    db_session.add_all([reporter, zone])
    await db_session.commit()
    await db_session.refresh(reporter)
    await db_session.refresh(zone)

    sighting = Sighting(user_id=reporter.id, zone_id=zone.id, image_path="cat.png")
    db_session.add(sighting)
    await db_session.commit()
    await db_session.refresh(sighting)

    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.delete(f"/admin/sightings/{sighting.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_missing_sighting_returns_404(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.delete("/admin/sightings/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_moderator_cannot_list_users(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.get("/admin/users")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.get("/admin/users")

    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "admin@example.com" in emails


@pytest.mark.asyncio
async def test_admin_can_promote_user_to_moderator(admin_app, admin_client, db_session):
    target = User(email="member@example.com", role=UserRole.USER)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.patch(
        f"/admin/users/{target.id}/role", json={"role": "moderator"}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "moderator"


@pytest.mark.asyncio
async def test_moderator_cannot_change_roles(admin_app, admin_client, db_session):
    target = User(email="member@example.com", role=UserRole.USER)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    await _login_as(admin_app, db_session, UserRole.MODERATOR)

    response = admin_client.patch(
        f"/admin/users/{target.id}/role", json={"role": "admin"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_role_of_missing_user_returns_404(admin_app, admin_client, db_session):
    await _login_as(admin_app, db_session, UserRole.ADMIN)

    response = admin_client.patch("/admin/users/999/role", json={"role": "moderator"})

    assert response.status_code == 404
