from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app as main_app
from app.routers.ai import router
from app.services.llm_client import FakeLLMClient
from app.services.llm_client_factory import get_llm_client
from app.services.sighting_context import SightingContext, ZoneCount


async def fake_db():
    yield "test-db"


async def fake_current_user():
    return SimpleNamespace(id=42)


def create_client(llm: FakeLLMClient, *, authenticated: bool = True) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = fake_db
    if authenticated:
        app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_llm_client] = lambda: llm
    return TestClient(app)


def test_get_diary_returns_grounded_entry() -> None:
    llm = FakeLLMClient(response="I inspected the Garden today.")
    context = SightingContext(
        date="2026-08-13",
        total_sightings=2,
        zones=[ZoneCount(name="Garden", count=2)],
        hours=[10],
    )

    with patch(
        "app.routers.ai.build_daily_context",
        new=AsyncMock(return_value=context),
    ) as build_context:
        response = create_client(llm).get("/ai/diary?date=2026-08-13")

    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-08-13",
        "content": "I inspected the Garden today.",
    }
    build_context.assert_awaited_once_with("test-db", date(2026, 8, 13))


def test_get_diary_rejects_invalid_date() -> None:
    response = create_client(FakeLLMClient()).get("/ai/diary?date=not-a-date")

    assert response.status_code == 422


def test_get_diary_requires_authentication() -> None:
    response = create_client(
        FakeLLMClient(), authenticated=False
    ).get("/ai/diary?date=2026-08-13")

    assert response.status_code == 401


def test_main_app_registers_diary_route() -> None:
    paths = {route.path for route in main_app.routes}

    assert "/ai/diary" in paths
