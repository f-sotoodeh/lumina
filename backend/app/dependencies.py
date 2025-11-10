# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status, Cookie
from app.core.security import decode_token
from app.models.user import User

async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user