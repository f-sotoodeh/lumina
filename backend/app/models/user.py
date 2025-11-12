# backend/app/models/user.py
from beanie import Document
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from pytz import UTC
from pymongo import IndexModel, ASCENDING

class User(Document):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = "en"  # 'en' | 'ru' | 'hy'

    otp: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    password_hash: Optional[str] = None
    is_admin: bool = False

    created_at: datetime = datetime.now(UTC)
    last_logged_in_at: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            "is_admin",
            "created_at",
            "last_logged_in_at",
        ]
