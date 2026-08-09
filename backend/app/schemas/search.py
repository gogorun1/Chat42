from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class SightingSortField(str, Enum):
    CREATED_AT = "created_at"
    ZONE = "zone"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SightingSearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    zone_name: str
    reporter_id: int
    reporter_email: str
    image_url: str
    created_at: datetime


class SightingSearchResult(BaseModel):
    items: list[SightingSearchOut]
    total: int
    page: int
    page_size: int