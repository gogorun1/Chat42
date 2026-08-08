from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class SightingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    image_url: str
    created_at: datetime
    zone: ZoneRead
