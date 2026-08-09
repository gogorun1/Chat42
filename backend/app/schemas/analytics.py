from pydantic import BaseModel


class ZoneActivityOut(BaseModel):
    zone_id: int
    zone_name: str
    count: int


class DailyTrendOut(BaseModel):
    date: str  # ISO date, e.g. "2026-08-09"
    count: int


class TopReporterOut(BaseModel):
    user_id: int
    email: str
    count: int


class AnalyticsSummaryOut(BaseModel):
    total_sightings: int
    window_days: int
    zone_activity: list[ZoneActivityOut]
    daily_trend: list[DailyTrendOut]
    top_reporters: list[TopReporterOut]