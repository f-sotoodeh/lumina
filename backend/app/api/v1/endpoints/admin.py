# backend/app/api/v1/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.user import User
from app.models.deck import Deck
from app.schemas.admin import (
    AdminUserListData, AdminUserEmailUpdateData,
    AdminDeckListData, AdminDeckCountData
)
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import require_admin
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

class UpdateEmailRequest(BaseModel):
    email: EmailStr

@router.get("/users", response_model=APIResponse[AdminUserListData])
async def get_all_users(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin)
):
    """Get all users (admin only)"""
    users = await User.find().skip(offset).limit(limit).to_list()
    total = await User.count()
    
    from app.schemas.admin import AdminUserItem
    users_data = [
        AdminUserItem(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_logged_in_at=user.last_logged_in_at
        )
        for user in users
    ]
    
    pages = (total + limit - 1) // limit
    page = offset // limit + 1
    
    return api_response(
        request=request,
        success=True,
        data=AdminUserListData(
            users=users_data,
            total=total,
            page=page,
            pages=pages
        ).model_dump()
    )

@router.put("/users/{user_id}/email", response_model=APIResponse[AdminUserEmailUpdateData])
async def change_user_email(
    request: Request,
    user_id: str,
    payload: UpdateEmailRequest,
    current_admin: User = Depends(require_admin)
):
    """Change user email (admin only)"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="auth.user_not_found"
            )
        )
    
    # Check if email already exists
    existing = await User.find_one({"email": payload.email})
    if existing and str(existing.id) != user_id:
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="auth.email_already_registered"
            )
        )
    
    user.email = payload.email
    await user.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="admin.user_email_updated",
        data=AdminUserEmailUpdateData(
            id=str(user.id),
            email=user.email
        ).model_dump()
    )

@router.get("/decks", response_model=APIResponse[AdminDeckListData])
async def get_all_decks(
    request: Request,
    user_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin)
):
    """Get all decks with optional user filter (admin only)"""
    query = {}
    if user_id:
        query["owner_id"] = user_id
    
    decks = await Deck.find(query).skip(offset).limit(limit).to_list()
    total = await Deck.find(query).count()
    
    from app.schemas.admin import AdminDeckItem
    decks_data = [
        AdminDeckItem(
            id=str(deck.id),
            title=deck.title,
            owner_id=deck.owner_id,
            is_public=deck.is_public,
            created_at=deck.created_at,
            updated_at=deck.updated_at
        )
        for deck in decks
    ]
    
    pages = (total + limit - 1) // limit
    page = offset // limit + 1
    
    return api_response(
        request=request,
        success=True,
        data=AdminDeckListData(
            decks=decks_data,
            total=total,
            page=page,
            pages=pages
        ).model_dump()
    )

@router.get("/decks/count", response_model=APIResponse[AdminDeckCountData])
async def get_decks_count(
    request: Request,
    current_admin: User = Depends(require_admin)
):
    """Get decks count per user (admin only)"""
    # Aggregate decks by owner_id
    pipeline = [
        {"$group": {"_id": "$owner_id", "count": {"$sum": 1}}}
    ]
    
    # Execute aggregation
    results = await Deck.aggregate(pipeline).to_list()
    
    # Convert to dict
    counts = {item["_id"]: item["count"] for item in results}
    
    return api_response(
        request=request,
        success=True,
        data=AdminDeckCountData(counts=counts).model_dump()
    )

