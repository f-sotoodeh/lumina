from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, UTC
from app.core.config import settings
from app.core.email import send_otp_email
from app.schemas.auth import AuthTokenData, AuthResponseData, UserData
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
import secrets
from app.core.security import (
    create_access_token, create_refresh_token,
    verify_password, get_password_hash, decode_token
)

router = APIRouter()
SECURE = settings.ENVIRONMENT.lower().startswith('prod')


def validate_password(password: str) -> bool:
    """Validate password: min 8 chars, uppercase, lowercase, number"""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

@router.post('/register', response_model=APIResponse[AuthResponseData])
async def register(
    request: RegisterRequest, 
    response: Response,
):
    existing = await User.find_one({'email': request.email})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=api_response(
                request=request,
                success=False,
                message_key="auth.email_already_registered",
                errors=[{"field": "email", "message": "auth.email_already_registered"}]
            )
        )
    
    # Validate password
    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="validation.password_weak",
                errors=[{"field": "password", "message": "validation.password_weak"}]
            )
        )

    hashed = get_password_hash(request.password)
    user = User(
        email=request.email, 
        first_name=request.first_name, 
        last_name=request.last_name, 
        password_hash=hashed
    )
    user.last_logged_in_at = datetime.now(UTC)
    await user.insert()

    access = create_access_token({'sub': str(user.id), 'role': 'admin' if user.is_admin else 'user'})
    refresh = create_refresh_token({'sub': str(user.id), 'role': 'admin' if user.is_admin else 'user'})

    response.set_cookie(
        key='access_token', 
        value=access, 
        httponly=True, 
        secure=SECURE, 
        samesite='lax', 
        max_age=15*60,
    )
    response.set_cookie(
        key='refresh_token', 
        value=refresh, 
        httponly=True, 
        secure=SECURE, 
        samesite='lax', 
        max_age=7*24*3600,
    )
    return api_response(
        request=request,
        success=True,
        data=AuthResponseData(
            access_token=access,
            refresh_token=refresh,
            token_type='bearer',
            user=UserData(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                preferred_language=user.preferred_language or "en"
            )
        ).model_dump()
    )

@router.post('/login', response_model=APIResponse[AuthResponseData])
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(), 
    response: Response = None
):
    user = await User.find_one({'email': form.username})
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=401, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.invalid_credentials',
            )
        )

    user.last_logged_in_at = datetime.now(UTC)
    await user.save()

    access = create_access_token({"sub": str(user.id), 'role': 'admin' if user.is_admin else 'user'})
    refresh = create_refresh_token({"sub": str(user.id), 'role': 'admin' if user.is_admin else 'user'})

    response.set_cookie(
        key='access_token', 
        value=access, 
        httponly=True, 
        secure=SECURE, 
        samesite='lax', 
        max_age=15*60
    )
    response.set_cookie(
        key='refresh_token', 
        value=refresh, 
        httponly=True, 
        secure=SECURE, 
        samesite='lax', 
        max_age=7*24*3600
    )
    return api_response(
        request=request,
        success=True,
        data=AuthResponseData(
            access_token=access,
            refresh_token=refresh,
            token_type='bearer',
            user=UserData(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                preferred_language=user.preferred_language or "en"
            )
        ).model_dump()
    )

@router.post('/refresh', response_model=APIResponse[AuthTokenData])
async def refresh(
    request: Request,
    response: Response, 
    refresh_token: str = Cookie(None)
):
    if not refresh_token:
        raise HTTPException(
            status_code=401, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.no_refresh_token',
            )
        )
    payload = decode_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        raise HTTPException(
            status_code=401, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.invalid_refresh_token',
            )
        )
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=401, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.user_not_found',
            )
        )

    access = create_access_token({"sub": payload["sub"], 'role': 'admin' if user.is_admin else 'user'})
    response.set_cookie(
        key='access_token', 
        value=access, 
        httponly=True, 
        secure=SECURE, 
        samesite='lax', 
        max_age=15*60
    )
    return api_response(
        request=request,
        success=True,
        data=AuthTokenData(
            access_token=access,
            refresh_token=refresh_token,
            token_type='bearer'
        ).model_dump()
    )

@router.post('/logout', response_model=APIResponse[EmptyData])
async def logout(
    request: Request,
    response: Response,
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return api_response(
        request=request,
        success=True,
        message_key='auth.logged_out',
        data=EmptyData().model_dump()
    )

@router.post('/forgot-password', response_model=APIResponse[EmptyData])
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
):
    user = await User.find_one({"email": payload.email})
    lang = request.headers.get("accept-language", "en")[:2]

    if not user:
        # For security, always returned "email sent" even if user doesn't exist
        return api_response(
            request=request,
            success=True,
            message_key='auth.otp_sent',
            data=EmptyData().model_dump()
        )

    # Generate 6 digit OTP
    otp = f"{secrets.randbelow(900000) + 100000}"
    user.otp = otp
    user.otp_expiry = datetime.now(UTC) + timedelta(minutes=15)
    await user.save()
    background_tasks.add_task(send_otp_email, background_tasks, user.email, otp, lang)
    return api_response(
        request=request,
        success=True,
        message_key='auth.otp_sent',
        data=EmptyData().model_dump()
    )

@router.post('/reset-password', response_model=APIResponse[EmptyData])
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest
):
    user = await User.find_one({"email": payload.email})
    if not user:
        raise HTTPException(
            status_code=400, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.invalid_request',
            )
        )
    
    # Validate new password
    if not validate_password(payload.new_password):
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="validation.password_weak",
                errors=[{"field": "new_password", "message": "validation.password_weak"}]
            )
        )
    
    if user.otp != payload.otp or not user.otp_expiry or user.otp_expiry < datetime.now(UTC):
        raise HTTPException(
            status_code=400, 
            detail=api_response(
                request=request,
                success=False,
                message_key='auth.invalid_otp',
            )
        )

    # Update password and remove OTP
    user.password_hash = get_password_hash(payload.new_password)
    user.otp = None
    user.otp_expiry = None
    await user.save()

    return api_response(
        request=request,
        success=True,
        message_key='auth.password_reset_success',
        data=EmptyData().model_dump()
    )

