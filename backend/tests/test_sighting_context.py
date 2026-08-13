from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.sighting_context import build_daily_context


@pytest.mark.asyncio
async def test_build_daily_context_summarizes_sightings() -> None:
    db = AsyncMock()

    zone_result = Mock()
    zone_result.all.return_value = [("Garden", 2), ("Cafeteria", 1)]

    hour_result = Mock()
    hour_result.all.return_value = [(18,), (10,), (18,), (13,)]

    db.execute.side_effect = [zone_result, hour_result]

    context = await build_daily_context(db, date(2026, 8, 13))

    assert context.to_dict() == {
        "date": "2026-08-13",
        "total_sightings": 3,
        "zones": [
            {"name": "Garden", "count": 2},
            {"name": "Cafeteria", "count": 1},
        ],
        "hours": [10, 13, 18],
    }


@pytest.mark.asyncio
async def test_build_daily_context_returns_empty_context() -> None:
    db = AsyncMock()

    zone_result = Mock()
    zone_result.all.return_value = []

    hour_result = Mock()
    hour_result.all.return_value = []

    db.execute.side_effect = [zone_result, hour_result]

    context = await build_daily_context(db, date(2026, 8, 14))

    assert context.to_dict() == {
        "date": "2026-08-14",
        "total_sightings": 0,
        "zones": [],
        "hours": [],
    }
