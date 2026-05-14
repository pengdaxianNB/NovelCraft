from pydantic import BaseModel
from datetime import datetime
import uuid


class RagDocumentResponse(BaseModel):
    id: uuid.UUID
    novel_id: uuid.UUID
    filename: str
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class RagSearchRequest(BaseModel):
    novel_id: str | None = None
    query: str
    top_k: int = 5


class RagSearchResult(BaseModel):
    id: str
    content: str
    metadata: dict
    similarity: float
