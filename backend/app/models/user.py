# backend/app/models/user.py
from beanie import Document
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from pytz import UTC

class User(Document):
    email: EmailStr
    name: Optional[str] = None
    password_hash: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = datetime.now(UTC)
    last_logged_in_at: Optional[datetime] = None

    class Settings:
        name = "users"