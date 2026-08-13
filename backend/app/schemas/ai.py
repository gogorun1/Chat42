from datetime import date

from pydantic import BaseModel


class DiaryRead(BaseModel):
    date: date
    content: str
