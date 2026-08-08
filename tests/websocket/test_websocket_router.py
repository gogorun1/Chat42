"""
Run:
    pytest tests/websocket/test_websocket_router.py -v

Covers:
- websocket origin allow-list logic
- handshake rejection cases
- authenticated websocket connection lifecycle
"""

from __future__ import annotations

from unittest.mock import  AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.constants import ACCESS_TOKEN_COOKIE
from app.routers.websocket import _origin_allowed, router
from app.models.user import User

def _fake_websocket(origin: str | None):
    websocket = MagicMock()
    websocket.headers = {"origin": origin} if origin else {}
    return websocket


class FakeSettings:
    cors_origins = [
        "https://localhost",
        "https://192.168.1.42",
    ]


@pytest.fixture
def websocket_app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(websocket_app):
    return TestClient(websocket_app)


# -------------------------
# Origin validation
# -------------------------

@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_allowed_origin_passes(mock_settings):
    assert _origin_allowed(
        _fake_websocket("https://localhost")
    )


@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_configured_lan_origin_passes(mock_settings):
    assert _origin_allowed(
        _fake_websocket("https://192.168.1.42")
    )


@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_unknown_origin_rejected(mock_settings):
    assert not _origin_allowed(
        _fake_websocket("https://evil.example.com")
    )


@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_missing_origin_allowed(mock_settings):
    assert _origin_allowed(
        _fake_websocket(None)
    )


# -------------------------
# Handshake rejection
# -------------------------

@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_rejects_disallowed_origin(mock_settings, client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/sightings",
            headers={
                "origin": "https://evil.example.com"
            },
        ):
            pass

    assert exc.value.code == 1008


@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_rejects_missing_cookie(mock_settings, client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/sightings",
            headers={
                "origin": "https://localhost"
            },
        ):
            pass

    assert exc.value.code == 1008


@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_rejects_invalid_token(mock_settings, client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            "/ws/sightings",
            headers={
                "origin": "https://localhost"
            },
            cookies={
                ACCESS_TOKEN_COOKIE: "invalid-token"
            },
        ):
            pass

    assert exc.value.code == 1008

@patch(
    "app.routers.websocket.get_settings",
    return_value=FakeSettings(),
)
def test_authenticated_user_can_connect(mock_settings, client):
    fake_user = User(
        id=1,
        email="test@example.com",
        password_hash="fake",
    )

    with patch(
        "app.routers.websocket._authenticate",
        new=AsyncMock(return_value=fake_user),
    ):
        with client.websocket_connect(
            "/ws/sightings",
            headers={
                "origin": "https://localhost"
            },
            cookies={
                ACCESS_TOKEN_COOKIE: "anything"
            },
        ):
            pass

