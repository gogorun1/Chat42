from pydantic import BaseModel
from datetime import datetime

class ZoneActivityOut(BaseModel):
    zone_id: int
    zone_name: str
    count: int

class RecentSightingOut(BaseModel):
    id: int
    zone_id: int
    zone_name: str
    reporter: str
    image_url: str
    created_at: datetime


class DailyTrendOut(BaseModel):
    date: str  # ISO date, e.g. "2026-08-09"
    count: int


class TopReporterOut(BaseModel):
    user_id: int
    email: str #change to username when we add usernames
    count: int


class AnalyticsSummaryOut(BaseModel):
    total_sightings: int
    period_sightings: int
    window_start: str
    window_end: str | None 
    zone_activity: list[ZoneActivityOut]
    daily_trend: list[DailyTrendOut]
    top_reporters: list[TopReporterOut]
    recent_sightings: list[RecentSightingOut]