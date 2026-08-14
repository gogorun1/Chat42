from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserRole


class ZoneCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)


class ZoneUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)


class SightingZoneUpdate(BaseModel):
    zone_id: int


class UserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    ft_login: str | None
    role: UserRole
