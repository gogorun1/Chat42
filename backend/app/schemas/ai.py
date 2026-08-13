from datetime import date

from pydantic import BaseModel, Field, field_validator


class DiaryRead(BaseModel):
    date: date
    content: str


class QuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=300)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank")
        return value
