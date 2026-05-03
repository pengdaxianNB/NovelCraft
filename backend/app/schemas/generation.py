from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class GenerateOutlineRequest(BaseModel):
    level: str = Field(default="chapter")
    parent_id: str | None = None
    count: int = Field(default=5, ge=1, le=20)


class GenerateChapterRequest(BaseModel):
    outline_id: str | None = None
    chapter_number: int | None = None
    words_per_chapter: int | None = None


class GenerationTaskResponse(BaseModel):
    id: str
    novel_id: str
    task_type: str
    target_id: str | None
    status: str
    progress: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
