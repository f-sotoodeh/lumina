# backend/app/models/deck.py
from beanie import Document, Link
from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4
from pytz import UTC
from pymongo import TEXT


class Deck(Document):
    # data
    title: str
    order: List[str] = []  # list of Step IDs (string)
    is_public: bool = False
    preview_url: str = str(uuid4())

    # settings
    background_color: str = "#ffffff"
    data_transition_duration: int = 1000
    data_width: int = 1024
    data_height: int = 768
    data_perspective: int = 1000

    # overview
    has_overview: bool = True
    overview_x: float = 0.0
    overview_y: float = 0.0
    overview_z: float = 0.0
    overview_scale: float = 1.0

    # meta
    owner_id: str
    thumbnail_url: Optional[str] = None
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)

    class Settings:
        name = "decks"
        indexes = [
            [("title", TEXT)],
            "is_public",
            "owner_id",
            "created_at",
            "updated_at"
        ]