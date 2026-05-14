from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, max_length=300)
    content: str | None = None


class ChapterReviewRequest(BaseModel):
    content: str | None = None


class ChapterReviewResponse(BaseModel):
    passed: bool
    issues: list[dict[str, Any]]
    summary: str
    rag_hits: list[dict[str, Any]] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)


class ChapterResponse(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    outline_id: uuid.UUID | None
    chapter_number: int
    title: str
    content: str | None
    word_count: int
    status: str
    generation_meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
