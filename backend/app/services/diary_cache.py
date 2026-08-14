from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diary_entry import DiaryEntry
from app.services.diary_service import generate_diary
from app.services.llm_client import LLMClient
from app.services.sighting_context import SightingContext, build_daily_context


async def get_or_create_diary(
    db: AsyncSession,
    day: date,
    llm: LLMClient,
    *,
    context: SightingContext | None = None,
) -> DiaryEntry:
    result = await db.execute(select(DiaryEntry).where(DiaryEntry.date == day))
    cached = result.scalar_one_or_none()
    if cached is not None:
        return cached

    context = context or await build_daily_context(db, day)
    entry = DiaryEntry(date=day, content=await generate_diary(context, llm))
    db.add(entry)
    try:
        await db.commit()
        return entry
    except IntegrityError:
        await db.rollback()
        result = await db.execute(select(DiaryEntry).where(DiaryEntry.date == day))
        return result.scalar_one()
