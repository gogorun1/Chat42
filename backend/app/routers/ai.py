import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai import DiaryRead, QuestionCreate
from app.services.diary_cache import get_or_create_diary
from app.services.llm_client import LLMClient
from app.services.llm_client_factory import get_llm_client
from app.services.question_service import stream_answer
from app.services.rate_limiter import RateLimiter
from app.services.sighting_context import build_daily_context


router = APIRouter(prefix="/ai", tags=["ai"])
question_limiter = RateLimiter(limit=10, window_seconds=60)
campus_timezone = ZoneInfo("Europe/Paris")


@router.get("/diary", response_model=DiaryRead)
async def get_diary(
    day: date | None = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> DiaryRead:
    today = datetime.now(campus_timezone).date()
    day = day or today
    entry = await get_or_create_diary(db, day, llm)
    return DiaryRead(date=entry.date, content=entry.content)


@router.post("/questions")
async def ask_question(
    payload: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    if not question_limiter.allow(current_user.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many questions. Try again in a minute.",
        )

    context = await build_daily_context(db, datetime.now(campus_timezone).date())

    async def events():
        async for chunk in stream_answer(payload.question, context, llm):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
