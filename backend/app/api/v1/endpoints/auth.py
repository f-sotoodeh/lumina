from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User
from pydantic import BaseModel, EmailStr
from datetime import datetime, UTC
from app.core.security import (
    create_access_token, create_refresh_token,
    verify_password, get_password_hash, decode_token
)

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, response: Response):
    existing = await User.find_one({"email": request.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(request.password)
    user = User(email=request.email, name=request.name, password_hash=hashed)
    await user.insert()

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token", value=access, httponly=True, secure=False, samesite="lax", max_age=15*60
    )
    response.set_cookie(
        key="refresh_token", value=refresh, httponly=True, secure=False, samesite="lax", max_age=7*24*3600
    )
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    user = await User.find_one({"email": form.username})
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_logged_in_at = datetime.now(UTC)
    await user.save()

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    response.set_cookie(
        key="access_token", value=access, httponly=True, secure=False, samesite="lax", max_age=15*60
    )
    response.set_cookie(
        key="refresh_token", value=refresh, httponly=True, secure=False, samesite="lax", max_age=7*24*3600
    )
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/refresh")
async def refresh(response: Response, refresh_token: str = ""):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token({"sub": payload["sub"]})
    response.set_cookie(
        key="access_token", value=access, httponly=True, secure=False, samesite="lax", max_age=15*60
    )
    return {"access_token": access}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"msg": "Logged out"}