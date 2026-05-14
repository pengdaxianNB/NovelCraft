from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class OutlineCreate(BaseModel):
    level: str = Field(..., max_length=20)
    parent_id: str | None = None
    sequence: int = 0
    title: str = Field(..., max_length=300)
    summary: str | None = None


class OutlineUpdate(BaseModel):
    title: str | None = Field(None, max_length=300)
    summary: str | None = None
    status: str | None = None
    sequence: int | None = None


class OutlineReorder(BaseModel):
    new_sequence: int
    new_parent_id: str | None = None


class OutlineResponse(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    level: str
    parent_id: uuid.UUID | None
    sequence: int
    title: str
    summary: str | None
    status: str
    children: list["OutlineResponse"] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
