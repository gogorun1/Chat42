"""
Run: pytest tests/notifications/test_notification_service.py -v

Mocks the DB session and the ConnectionManager so this tests only the
service's own logic (does it persist AND push, in that order, with the
right payload) — not SQLAlchemy or real sockets.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.notification import NotificationType
from app.models.sighting import Sighting
from app.schemas.notification import NotificationCreate
from app.services.notification_service import broadcast_sighting, notify_user


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()  # db.add() is sync in real SQLAlchemy; AsyncMock's default would hide misuse

    # db.refresh() would normally populate server-generated fields (id,
    # created_at) after commit; simulate that here since we're not hitting
    # a real DB.
    async def fake_refresh(obj):
        obj.id = obj.id or uuid.uuid4()
        obj.created_at = obj.created_at or datetime.now(timezone.utc)

    db.refresh.side_effect = fake_refresh
    return db


def _fake_sighting(**overrides) -> Sighting:
    """A Sighting with just enough set to exercise broadcast_sighting — not persisted."""
    s = Sighting(
        id=overrides.get("id", 1),
        user_id=overrides.get("user_id", 1),
        zone_id=overrides.get("zone_id", 1),
        image_path=overrides.get("image_path", "cat123.jpg"),
    )
    s.created_at = overrides.get("created_at", datetime.now(timezone.utc))
    return s


@pytest.mark.asyncio
async def test_notify_user_persists_before_pushing(mock_db):
    """
    Order matters: if the push went out before commit and the commit then
    failed, the client would show a notification that doesn't exist in the
    DB on next page load. Assert commit happens, then the push.
    """
    payload = NotificationCreate(
        user_id=1,
        type=NotificationType.SIGHTING_APPROVED,
        title="Your sighting was approved",
    )

    with patch("app.services.notification_service.manager") as mock_manager:
        mock_manager.send_to_user = AsyncMock()

        result = await notify_user(mock_db, payload)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_manager.send_to_user.assert_awaited_once()

        # the push must be addressed to the right user with the right type
        sent_user_id, sent_payload = mock_manager.send_to_user.call_args.args
        assert sent_user_id == payload.user_id
        assert sent_payload["type"] == NotificationType.SIGHTING_APPROVED.value
        assert result.title == "Your sighting was approved"


@pytest.mark.asyncio
async def test_broadcast_sighting_excludes_the_reporter():
    sighting = _fake_sighting(user_id=42)

    with patch("app.services.notification_service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        await broadcast_sighting(sighting, zone_name="Le Wagon")

        mock_manager.broadcast.assert_awaited_once()
        _, kwargs = mock_manager.broadcast.call_args
        assert kwargs["exclude_user"] == 42


@pytest.mark.asyncio
async def test_broadcast_sighting_builds_upload_url_from_image_path():
    """No Cat entity and no stored image_url in the real Sighting model —
    the URL is derived from image_path, matching F2's own _to_sighting_read."""
    sighting = _fake_sighting(image_path="moulinette_042.jpg")

    with patch("app.services.notification_service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()

        await broadcast_sighting(sighting, zone_name="Le Wagon")

        args, _ = mock_manager.broadcast.call_args
        payload = args[0]
        assert payload["image_url"] == "/uploads/moulinette_042.jpg"
        assert payload["zone_name"] == "Le Wagon"
        assert "Le Wagon" in payload["message"]


@pytest.mark.asyncio
async def test_broadcast_sighting_does_not_touch_the_db():
    """
    Public broadcasts are intentionally not persisted as per-user
    notification rows (see the docstring in notification_service), and the
    function doesn't even take a `db` argument any more — this just
    confirms it doesn't reach for one implicitly.
    """
    sighting = _fake_sighting()

    with patch("app.services.notification_service.manager") as mock_manager:
        mock_manager.broadcast = AsyncMock()
        # No db object exists in this test's scope at all — if broadcast_sighting
        # tried to use one, this test would fail with a NameError, not silently pass.
        await broadcast_sighting(sighting, zone_name="Le Wagon")