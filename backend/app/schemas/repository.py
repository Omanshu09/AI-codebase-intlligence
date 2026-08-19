from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RepositoryIngestRequest(BaseModel):
    repo_url: str = Field(..., description="Public GitHub HTTPS URL, e.g. https://github.com/user/project")


class RepositoryOut(BaseModel):
    id: str
    name: str
    url: str
    status: str
    file_count: int
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
