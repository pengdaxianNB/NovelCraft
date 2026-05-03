from pydantic import BaseModel, Field
from datetime import datetime


class WorldSettingCreate(BaseModel):
    category: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    content: str = Field(...)


class WorldSettingUpdate(BaseModel):
    category: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=200)
    content: str | None = None


class WorldSettingResponse(BaseModel):
    id: str
    novel_id: str
    category: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
