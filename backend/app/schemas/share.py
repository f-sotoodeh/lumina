# backend/app/schemas/share.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

class ShareItem(BaseModel):
    id: str
    share_with: str
    access_level: str
    shared_at: datetime

class ShareListData(BaseModel):
    shares: List[ShareItem]

