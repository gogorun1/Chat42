from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationType

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: NotificationType
    title: str
    body: str | None
    data: dict[str, Any]
    is_read: bool
    created_at: datetime

class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int
    total: int
    page: int
    page_size: int

class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    body: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)