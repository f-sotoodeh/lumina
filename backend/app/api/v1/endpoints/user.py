# backend/app/api/v1/endpoints/user.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Response
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate, UserAvatarUploadData
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user
from app.utils.minio_client import upload_avatar, delete_avatar, get_presigned_url
import hashlib

router = APIRouter()

# 20 beautiful colors for avatar fallback
AVATAR_COLORS = [
    '#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#6366F1',
    '#8B5CF6', '#EC4899', '#06B6D4', '#14B8A6', '#84CC16',
    '#F97316', '#EAB308', '#22C55E', '#0EA5E9', '#6366F1',
    '#A855F7', '#F43F5E', '#64748B', '#059669', '#7C3AED'
]

def get_avatar_color(email: str) -> str:
    """Get consistent color for email address"""
    hash_value = int(hashlib.md5(email.encode()).hexdigest(), 16)
    return AVATAR_COLORS[hash_value % len(AVATAR_COLORS)]

def get_initials(first_name: str | None, last_name: str | None) -> str:
    """Get initials from name"""
    initials = ""
    if first_name:
        initials += first_name[0].upper()
    if last_name:
        initials += last_name[0].upper()
    return initials or "?"

def generate_avatar_svg(email: str, first_name: str | None, last_name: str | None) -> str:
    """Generate SVG avatar with initials and color"""
    color = get_avatar_color(email)
    initials = get_initials(first_name, last_name)
    
    svg = f'''<svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="{color}"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="24" fill="white" text-anchor="middle" dominant-baseline="central">{initials}</text>
</svg>'''
    return svg

@router.get("/me", response_model=APIResponse[UserOut])
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return api_response(
        request=request,
        success=True,
        data=UserOut.model_validate(current_user).model_dump()
    )

@router.put("/me", response_model=APIResponse[UserOut])
async def update_profile(
    request: Request,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    # Email change not allowed for regular users
    if payload.email and payload.email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="user.email_change_not_allowed"
            )
        )
    
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    
    await current_user.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="user.profile_updated",
        data=UserOut.model_validate(current_user).model_dump()
    )

@router.post("/me/avatar", response_model=APIResponse[UserAvatarUploadData])
async def upload_user_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload user avatar"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.invalid_file_type"
            )
        )
    
    # Validate file size (max 5MB)
    file_data = await file.read()
    if len(file_data) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.file_too_large"
            )
        )
    
    # Delete old avatar if exists
    if current_user.avatar_url:
        delete_avatar(str(current_user.id))
    
    # Upload new avatar
    original_path, thumbnail_path = upload_avatar(
        str(current_user.id),
        file_data,
        file.content_type
    )
    
    # Get presigned URL for thumbnail
    thumbnail_url = get_presigned_url(thumbnail_path, expiry_days=7)
    
    # Update user
    current_user.avatar_url = thumbnail_url
    await current_user.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="user.avatar_uploaded",
        data=UserAvatarUploadData(avatar_url=thumbnail_url).model_dump()
    )

@router.delete("/me/avatar", response_model=APIResponse[EmptyData])
async def delete_user_avatar(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Delete user avatar"""
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.not_found"
            )
        )
    
    # Delete from MinIO
    delete_avatar(str(current_user.id))
    
    # Update user
    current_user.avatar_url = None
    await current_user.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="user.avatar_deleted",
        data=EmptyData().model_dump()
    )

@router.get("/me/avatar/fallback")
async def get_avatar_fallback(current_user: User = Depends(get_current_user)):
    """Get SVG avatar fallback"""
    svg = generate_avatar_svg(
        current_user.email,
        current_user.first_name,
        current_user.last_name
    )
    return Response(content=svg, media_type="image/svg+xml")

