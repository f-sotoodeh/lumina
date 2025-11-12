# backend/app/schemas/admin.py
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class AdminUserItem(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    is_admin: bool
    created_at: datetime
    last_logged_in_at: datetime | None

class AdminUserListData(BaseModel):
    users: List[AdminUserItem]
    total: int
    page: int
    pages: int

class AdminUserEmailUpdateData(BaseModel):
    id: str
    email: str

class AdminDeckItem(BaseModel):
    id: str
    title: str
    owner_id: str
    is_public: bool
    created_at: datetime
    updated_at: datetime

class AdminDeckListData(BaseModel):
    decks: List[AdminDeckItem]
    total: int
    page: int
    pages: int

class AdminDeckCountData(BaseModel):
    counts: Dict[str, int]

