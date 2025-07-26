from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from pathlib import Path

class DocumentUpload(BaseModel):
    filename: str
    content_type: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    content_type: str
    file_size: int
    uploaded_at: datetime
    indexed: bool = False

class DocumentQuery(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    document_id: str
    filename: str
    content: str
    score: float