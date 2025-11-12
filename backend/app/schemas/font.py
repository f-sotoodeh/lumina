# backend/app/schemas/font.py
from pydantic import BaseModel
from typing import List

class FontItem(BaseModel):
    family: str
    category: str | None = None

class FontListData(BaseModel):
    fonts: List[FontItem]

