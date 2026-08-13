from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.diary_entry import DiaryEntry
from app.services.diary_cache import get_or_create_diary
from app.services.llm_client import FakeLLMClient
from app.services.sighting_context import SightingContext


@pytest.mark.asyncio
async def test_returns_cached_diary_without_calling_llm() -> None:
    db = AsyncMock()
    result = Mock()
    result.scalar_one_or_none.return_value = DiaryEntry(
        date=date(2026, 8, 13), content="Cached diary"
    )
    db.execute.return_value = result
    llm = FakeLLMClient(response="New diary")

    entry = await get_or_create_diary(db, date(2026, 8, 13), llm)

    assert entry.content == "Cached diary"
    assert llm.prompts == []
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_generates_and_saves_missing_diary() -> None:
    db = AsyncMock()
    db.add = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result
    context = SightingContext(date="2026-08-13", total_sightings=0)
    llm = FakeLLMClient(response="A quiet day.")

    entry = await get_or_create_diary(
        db, date(2026, 8, 13), llm, context=context
    )

    assert entry.content == "A quiet day."
    db.add.assert_called_once_with(entry)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_winning_entry_after_concurrent_insert() -> None:
    db = AsyncMock()
    db.add = Mock()
    missing = Mock()
    missing.scalar_one_or_none.return_value = None
    winner = DiaryEntry(date=date(2026, 8, 13), content="Winning diary")
    found = Mock()
    found.scalar_one.return_value = winner
    db.execute.side_effect = [missing, found]
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    context = SightingContext(date="2026-08-13", total_sightings=0)

    entry = await get_or_create_diary(
        db,
        date(2026, 8, 13),
        FakeLLMClient(response="Losing diary"),
        context=context,
    )

    assert entry is winner
    db.rollback.assert_awaited_once()
