from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    repository_id: str
    question: str = Field(..., min_length=3)
    top_k: Optional[int] = None


class SourceChunk(BaseModel):
    file_path: str
    symbol: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    snippet: str
    score: float


class QueryResponse(BaseModel):
    id: str
    question: str
    answer: str
    sources: List[SourceChunk]
    created_at: datetime
