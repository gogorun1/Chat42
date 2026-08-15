from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
    correct_predictions: int
    score: int


class PredictionCreate(BaseModel):
    zone_id: int


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    target_date: date
    is_correct: bool | None
    created_at: datetime
