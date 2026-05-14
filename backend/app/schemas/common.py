from pydantic import BaseModel
from datetime import datetime
import uuid


class BaseResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
