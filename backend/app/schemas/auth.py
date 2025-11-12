# backend/app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional

class AuthTokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserData(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_language: Optional[str] = "en"

class AuthResponseData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserData

