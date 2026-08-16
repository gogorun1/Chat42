import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class NotificationType(str, enum.Enum):
    SIGHTING_NEARBY = "sighting_nearby"
    SIGHTING_APPROVED = "sighting_approved"
    SIGHTING_REJECTED = "sighting_rejected"
    SIGHTING_REMOVED = "sighting_removed"      # NEW: moderator/admin direct delete
    GUESS_RESULT = "guess_result"
    BADGE_EARNED = "badge_earned"
    FRIEND_REQUEST = "friend_request"
    ROLE_CHANGED = "role_changed"              # NEW: admin changes a user's role
    SYSTEM = "system"

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(140),
        nullable=False,
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="notifications",
    )

    @property
    def is_read(self) -> bool:
        return self.read_at is not None