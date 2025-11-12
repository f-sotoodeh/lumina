# backend/app/schemas/file.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FileOut(BaseModel):
    id: str
    user_id: str
    deck_id: str
    original_name: str
    minio_id: str
    url: str
    thumbnail_url: Optional[str]
    size: int
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    file_id: str
    url: str
    thumbnail_url: Optional[str]
    original_name: str

# Response models for file endpoints
class FileQuotaData(BaseModel):
    used: float
    limit: float
    unit: str

class FileGetData(BaseModel):
    id: str
    original_name: str
    url: str
    thumbnail_url: Optional[str]
    file_type: str
    size: int

class FileListData(BaseModel):
    files: List[FileOut]
    total: int
    page: int
    pages: int

class FileUploadListData(BaseModel):
    files: List[FileUploadResponse]

