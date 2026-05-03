from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, max_length=300)
    content: str | None = None


class ChapterResponse(BaseModel):
    id: str
    novel_id: str
    outline_id: str | None
    chapter_number: int
    title: str
    content: str | None
    word_count: int
    status: str
    generation_meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
