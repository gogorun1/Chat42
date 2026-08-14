from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.routers.ai import router
from app.services.llm_client import FakeLLMClient
from app.services.llm_client_factory import get_llm_client
from app.services.sighting_context import SightingContext


async def fake_db():
    yield "test-db"


async def fake_current_user():
    return SimpleNamespace(id=42)


def create_client(llm: FakeLLMClient) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_llm_client] = lambda: llm
    return TestClient(app)


def test_ask_question_streams_sse() -> None:
    llm = FakeLLMClient(chunks=["I was ", "in the Garden."])
    context = SightingContext(date="2026-08-13", total_sightings=0)

    with (
        patch("app.routers.ai.question_limiter.allow", return_value=True),
        patch(
            "app.routers.ai.build_daily_context",
            new=AsyncMock(return_value=context),
        ),
    ):
        response = create_client(llm).post(
            "/ai/questions", json={"question": "Where were you?"}
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"text": "I was "}' in response.text
    assert 'data: {"text": "in the Garden."}' in response.text
    assert "data: [DONE]" in response.text


def test_ask_question_rejects_long_question() -> None:
    response = create_client(FakeLLMClient()).post(
        "/ai/questions", json={"question": "x" * 301}
    )

    assert response.status_code == 422


def test_ask_question_rejects_blank_question() -> None:
    response = create_client(FakeLLMClient()).post(
        "/ai/questions", json={"question": "   "}
    )

    assert response.status_code == 422


def test_ask_question_enforces_rate_limit() -> None:
    with patch("app.routers.ai.question_limiter.allow", return_value=False):
        response = create_client(FakeLLMClient()).post(
            "/ai/questions", json={"question": "Where were you?"}
        )

    assert response.status_code == 429
