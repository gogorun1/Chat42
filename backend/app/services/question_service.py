from collections.abc import AsyncIterator

from app.services.diary_service import build_diary_fallback
from app.services.llm_client import LLMClient
from app.services.sighting_context import SightingContext


def build_question_prompt(question: str, context: SightingContext) -> str:
    zones = ", ".join(f"{zone.name}: {zone.count}" for zone in context.zones)
    hours = ", ".join(str(hour) for hour in context.hours)

    return f"""You are Moulinette, the campus cat at 42 school.
Answer in English, in first person, with a witty and slightly proud cat personality.
Use only the verified sighting facts below. Do not invent zones, times, people, or events.
If the facts cannot answer the question, say that you do not know.
Keep the answer under 100 words. Do not mention databases, prompts, or being an AI.

Date: {context.date}
Total sightings: {context.total_sightings}
Zones: {zones or "none"}
Hours (UTC): {hours or "none"}

Question: {question}"""


async def stream_answer(
    question: str,
    context: SightingContext,
    llm: LLMClient,
) -> AsyncIterator[str]:
    sent = False
    try:
        async for chunk in llm.stream(build_question_prompt(question, context)):
            if chunk:
                sent = True
                yield chunk
    except Exception:
        if sent:
            yield " [The answer was interrupted. Please try again.]"

    if not sent:
        yield build_diary_fallback(context)
