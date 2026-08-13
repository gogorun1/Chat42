import pytest

from app.services.llm_client import FakeLLMClient
from app.services.question_service import stream_answer
from app.services.sighting_context import SightingContext, ZoneCount


@pytest.mark.asyncio
async def test_stream_answer_uses_grounded_context() -> None:
    context = SightingContext(
        date="2026-08-13",
        total_sightings=2,
        zones=[ZoneCount(name="Garden", count=2)],
        hours=[10, 13],
    )
    llm = FakeLLMClient(chunks=["I was ", "in the Garden."])

    chunks = [chunk async for chunk in stream_answer("Where were you?", context, llm)]

    assert chunks == ["I was ", "in the Garden."]
    prompt = llm.prompts[0]
    assert "Where were you?" in prompt
    assert "Garden: 2" in prompt
    assert "Do not invent" in prompt


@pytest.mark.asyncio
async def test_stream_answer_falls_back_on_empty_stream() -> None:
    context = SightingContext(date="2026-08-13", total_sightings=0)

    chunks = [
        chunk async for chunk in stream_answer(
            "Where were you?", context, FakeLLMClient(chunks=[])
        )
    ]

    assert chunks == ["Nobody spotted me today. Exactly as planned."]


@pytest.mark.asyncio
async def test_stream_answer_reports_interrupted_stream() -> None:
    context = SightingContext(date="2026-08-13", total_sightings=0)
    llm = FakeLLMClient(
        chunks=["I was answering"],
        stream_error=RuntimeError("connection lost"),
    )

    chunks = [chunk async for chunk in stream_answer("Where?", context, llm)]

    assert chunks == [
        "I was answering",
        " [The answer was interrupted. Please try again.]",
    ]
