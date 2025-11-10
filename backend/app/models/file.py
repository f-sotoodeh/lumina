# backend/app/models/file.py
from beanie import Document
from datetime import datetime
from pytz import UTC
from typing import Optional

class FileModel(Document):
    user_id: str
    deck_id: str
    original_name: str
    minio_id: str
    url: str
    thumbnail_url: Optional[str] = None
    size: int
    file_type: str
    created_at: datetime = datetime.now(UTC)

    class Settings:
        name = "files"