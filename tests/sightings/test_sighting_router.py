from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select

from app.core.deps import get_current_user
from app.main import app
from app.models.sighting import Sighting
from app.models.user import User
from app.models.zone import Zone
from app.routers import sightings as sightings_router
from app.services.cat_detection import CatDetectionResult, InvalidImageError


@pytest.fixture
async def sighting_context(db_session, override_db):
    user = User(email="reporter@example.com")
    zone = Zone(slug="garden", name="Garden")
    db_session.add_all([user, zone])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(zone)

    async def override_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_current_user
    return user, zone


@pytest.mark.asyncio
async def test_rejects_upload_when_detector_finds_no_cat(
    client,
    db_session,
    sighting_context,
    monkeypatch,
):
    _, zone = sighting_context

    detector = Mock()
    detector.detect.return_value = CatDetectionResult(
        is_cat=False,
        confidence=0.02,
        model="test-model",
    )
    monkeypatch.setattr(
        sightings_router,
        "get_cat_detector",
        lambda: detector,
    )

    response = client.post(
        "/sightings/",
        data={"zone_id": str(zone.id)},
        files={"image": ("empty.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 422
    assert "No cat detected" in response.json()["detail"]
    detector.detect.assert_called_once_with(b"image-bytes")

    result = await db_session.execute(select(Sighting))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_creates_sighting_when_detector_finds_cat(
    client,
    db_session,
    sighting_context,
    monkeypatch,
):
    user, zone = sighting_context

    detector = Mock()
    detector.detect.return_value = CatDetectionResult(
        is_cat=True,
        confidence=0.31,
        model="test-model",
    )
    monkeypatch.setattr(
        sightings_router,
        "get_cat_detector",
        lambda: detector,
    )

    save_upload = Mock(return_value="stored-cat.png")
    monkeypatch.setattr(
        sightings_router,
        "save_upload",
        save_upload,
    )

    broadcast = AsyncMock()
    monkeypatch.setattr(
        sightings_router,
        "broadcast_sighting",
        broadcast,
    )

    response = client.post(
        "/sightings/",
        data={"zone_id": str(zone.id)},
        files={"image": ("cat.png", b"cat-image-bytes", "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["zone_id"] == zone.id
    assert response.json()["image_url"] == "/uploads/stored-cat.png"

    detector.detect.assert_called_once_with(b"cat-image-bytes")
    save_upload.assert_called_once()
    broadcast.assert_awaited_once()

    result = await db_session.execute(select(Sighting))
    sighting = result.scalar_one()

    assert sighting.user_id == user.id
    assert sighting.zone_id == zone.id
    assert sighting.image_path == "stored-cat.png"


@pytest.mark.asyncio
async def test_rejects_upload_when_detector_cannot_decode_image(
    client,
    db_session,
    sighting_context,
    monkeypatch,
):
    _, zone = sighting_context
    detector = Mock()
    detector.detect.side_effect = InvalidImageError("Invalid image")
    monkeypatch.setattr(sightings_router, "get_cat_detector", lambda: detector)

    response = client.post(
        "/sightings/",
        data={"zone_id": str(zone.id)},
        files={"image": ("broken.png", b"not-an-image", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid image"
    detector.detect.assert_called_once_with(b"not-an-image")

    result = await db_session.execute(select(Sighting))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_rejects_unsupported_media_type_before_detection(
    client,
    sighting_context,
    monkeypatch,
):
    _, zone = sighting_context
    detector_factory = Mock()
    monkeypatch.setattr(sightings_router, "get_cat_detector", detector_factory)

    response = client.post(
        "/sightings/",
        data={"zone_id": str(zone.id)},
        files={"image": ("notes.txt", b"not-an-image", "text/plain")},
    )

    assert response.status_code == 415
    detector_factory.assert_not_called()


@pytest.mark.asyncio
async def test_rejects_unknown_zone_before_detection(
    client,
    sighting_context,
    monkeypatch,
):
    _, zone = sighting_context
    detector_factory = Mock()
    monkeypatch.setattr(sightings_router, "get_cat_detector", detector_factory)

    response = client.post(
        "/sightings/",
        data={"zone_id": str(zone.id + 1000)},
        files={"image": ("cat.png", b"cat-image-bytes", "image/png")},
    )

    assert response.status_code == 404
    detector_factory.assert_not_called()
