import pytest

from app.services.diary_service import generate_diary
from app.services.llm_client import FakeLLMClient
from app.services.sighting_context import SightingContext, ZoneCount


@pytest.mark.asyncio
async def test_generate_diary_uses_only_sighting_context() -> None:
    context = SightingContext(
        date="2026-08-13",
        total_sightings=3,
        zones=[
            ZoneCount(name="Garden", count=2),
            ZoneCount(name="Cafeteria", count=1),
        ],
        hours=[10, 13, 18],
    )
    llm = FakeLLMClient(response="I inspected the Garden twice today.")

    diary = await generate_diary(context, llm)

    assert diary == "I inspected the Garden twice today."
    prompt = llm.prompts[0]
    assert "2026-08-13" in prompt
    assert "Garden: 2" in prompt
    assert "Cafeteria: 1" in prompt
    assert "10, 13, 18" in prompt
    assert "Do not invent" in prompt


@pytest.mark.asyncio
async def test_generate_diary_handles_no_sightings() -> None:
    context = SightingContext(
        date="2026-08-14",
        total_sightings=0,
    )
    llm = FakeLLMClient(response="A quiet day. My privacy remains intact.")

    diary = await generate_diary(context, llm)

    assert diary == "A quiet day. My privacy remains intact."
    prompt = llm.prompts[0]
    assert "Total sightings: 0" in prompt
    assert "Zones: none" in prompt
    assert "Hours (UTC): none" in prompt


@pytest.mark.asyncio
async def test_generate_diary_falls_back_when_llm_fails() -> None:
    context = SightingContext(
        date="2026-08-13",
        total_sightings=2,
        zones=[ZoneCount(name="Garden", count=2)],
        hours=[10],
    )
    llm = FakeLLMClient(error=RuntimeError("Gemini unavailable"))

    diary = await generate_diary(context, llm)

    assert diary == "I was spotted 2 times today, mostly around Garden."


@pytest.mark.asyncio
async def test_generate_diary_falls_back_when_llm_returns_empty_text() -> None:
    context = SightingContext(
        date="2026-08-14",
        total_sightings=0,
    )
    llm = FakeLLMClient(response="")

    diary = await generate_diary(context, llm)

    assert diary == "Nobody spotted me today. Exactly as planned."
