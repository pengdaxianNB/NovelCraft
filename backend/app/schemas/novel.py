from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class StyleConfig(BaseModel):
    tone: str = "热血"
    pov: str = "第三人称"
    words_per_chapter: int = 3000
    custom_instructions: str = ""


class ScheduleConfig(BaseModel):
    enabled: bool = False
    cron: str = "0 */6 * * *"


class NovelCreate(BaseModel):
    title: str = Field(..., max_length=200)
    genre: str = Field(default="玄幻", max_length=50)
    synopsis: str | None = None
    style_config: StyleConfig = StyleConfig()
    schedule_config: ScheduleConfig = ScheduleConfig()


class NovelUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    genre: str | None = Field(None, max_length=50)
    synopsis: str | None = None
    status: str | None = None


class NovelStyleUpdate(BaseModel):
    tone: str | None = None
    pov: str | None = None
    words_per_chapter: int | None = None
    custom_instructions: str | None = None


class NovelResponse(BaseModel):
    id: uuid.UUID
    title: str
    genre: str
    synopsis: str | None
    style_config: dict[str, Any]
    schedule_config: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    chapter_count: int = 0
    published_count: int = 0
    model_config = {"from_attributes": True}
