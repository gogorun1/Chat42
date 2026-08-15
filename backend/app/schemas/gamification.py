from datetime import datetime

from pydantic import BaseModel


class BadgeRead(BaseModel):
    code: str
    name: str
    description: str
    awarded_at: datetime


class LeaderboardEntry(BaseModel):
    user_id: int
    display_name: str | None
    avatar_url: str | None
    sighting_count: int
    guess_points: int
    score: int


class GuessCreate(BaseModel):
    zone_id: int


class GuessResult(BaseModel):
    correct: bool
    guess_points: int
    actual_zone_id: int
