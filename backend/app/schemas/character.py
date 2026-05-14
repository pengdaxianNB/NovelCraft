from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class CharacterCreate(BaseModel):
    name: str = Field(..., max_length=100)
    role: str = Field(default="配角", max_length=50)
    profile: dict[str, Any] = {}


class CharacterUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    role: str | None = Field(None, max_length=50)
    profile: dict[str, Any] | None = None


class CharacterResponse(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    name: str
    role: str
    profile: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
