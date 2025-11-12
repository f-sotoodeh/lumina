from beanie import Document, Indexed
from datetime import datetime
from typing import Literal
from pytz import UTC

AccessLevel = Literal["Editor", "Commenter", "Viewer"]

class Share(Document):
    deck_id: str
    owner_id: str
    share_with: str
    shared_at: datetime = datetime.now(UTC)
    access_level: AccessLevel

    class Settings:
        name = "shares"
        indexes = [
            "deck_id",
            "owner_id",
            "share_with",
            "shared_at",
            "access_level",
        ]