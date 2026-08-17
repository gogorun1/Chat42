from app.services.llm_client import LLMClient
from app.services.sighting_context import SightingContext


def build_diary_prompt(context: SightingContext) -> str:
    zones = ", ".join(f"{zone.name}: {zone.count}" for zone in context.zones)
    hours = ", ".join(str(hour) for hour in context.hours)

    return f"""You are Moulinette, the campus cat at 42 school.
Write a short diary entry in English and in first person as a witty, slightly proud cat.
Use only the verified sighting facts below. Do not invent zones, times, people, or events.
Zone counts and hours are independent aggregates. Do not associate a specific hour with a specific zone.
Do not mention databases, prompts, or that you are an AI.

Date: {context.date}
Total sightings: {context.total_sightings}
Zones: {zones or "none"}
Hours (UTC): {hours or "none"}

Write 2 to 4 sentences."""


async def generate_diary(context: SightingContext, llm: LLMClient) -> str:
    try:
        diary = await llm.generate(build_diary_prompt(context))
        if diary.strip():
            return diary
    except Exception:
        pass

    return build_diary_fallback(context)


def build_diary_fallback(context: SightingContext) -> str:
    if not context.zones:
        return "Nobody spotted me today. Exactly as planned."

    return (
        f"I was spotted {context.total_sightings} times today, "
        f"mostly around {context.zones[0].name}."
    )
