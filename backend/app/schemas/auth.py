# backend/app/schemas/auth.py
from pydantic import BaseModel

class AuthTokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

