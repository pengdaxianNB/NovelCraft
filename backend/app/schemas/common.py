from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
