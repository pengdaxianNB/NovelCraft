from pydantic import BaseModel
from datetime import datetime


class RagDocumentResponse(BaseModel):
    id: str
    novel_id: str
    filename: str
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RagSearchResult(BaseModel):
    id: str
    content: str
    metadata: dict
    similarity: float
