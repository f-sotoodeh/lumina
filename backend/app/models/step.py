# backend/app/models/step.py
from beanie import Document
from typing import Optional
from datetime import datetime

class Step(Document):
    # position
    data_x: float = 0.0
    data_y: float = 0.0
    data_z: float = 0.0
    data_rotate: float = 0.0
    data_rotate_x: float = 0.0
    data_rotate_y: float = 0.0
    data_rotate_z: float = 0.0
    data_scale: float = 1.0

    # settings
    data_transition_duration: int = 1000
    is_slide: bool = True

    # data
    inner_html: str = "<h1>New Slide</h1>"
    notes: str = ""

    # meta
    user_id: str
    deck_id: str

    class Settings:
        name = "steps"