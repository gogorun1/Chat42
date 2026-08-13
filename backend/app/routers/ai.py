from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai import DiaryRead
from app.services.diary_service import generate_diary
from app.services.llm_client import LLMClient
from app.services.llm_client_factory import get_llm_client
from app.services.sighting_context import build_daily_context

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/diary", response_model=DiaryRead)
async def get_diary(
    day: date = Query(alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> DiaryRead:
    context = await build_daily_context(db, day)
    content = await generate_diary(context, llm)
    return DiaryRead(date=day, content=content)
