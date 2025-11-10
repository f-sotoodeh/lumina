# backend/app/models/comment.py
from beanie import Document
from datetime import datetime
from pytz import UTC

class Comment(Document):
    user_id: str
    deck_id: str
    step_id: str
    text: str
    is_edited: bool = False
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    class Settings:
        name = "comments"