from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class WorldSettingCreate(BaseModel):
    category: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    content: str = Field(...)


class WorldSettingUpdate(BaseModel):
    category: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=200)
    content: str | None = None


class WorldSettingConsistencyRequest(BaseModel):
    category: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    content: str = Field(...)


class WorldSettingConsistencyResponse(BaseModel):
    passed: bool
    issues: list[dict[str, Any]] = Field(default_factory=list)
    summary: str
    rag_hits: list[dict[str, Any]] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)


class WorldSettingResponse(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    category: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
