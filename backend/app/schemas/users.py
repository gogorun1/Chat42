from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=50)


class PublicProfileRead(BaseModel):
    id: int
    display_name: str | None
    avatar_url: str | None
    online: bool
