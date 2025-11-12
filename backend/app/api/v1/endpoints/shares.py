# backend/app/api/v1/endpoints/shares.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.deck import Deck
from app.models.share import Share, AccessLevel
from app.models.user import User
from app.schemas.share import ShareListData
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ShareDeckRequest(BaseModel):
    user_id: str
    access_level: AccessLevel

@router.post("/{deck_id}/share", response_model=APIResponse[EmptyData])
async def share_deck(
    request: Request,
    deck_id: str,
    payload: ShareDeckRequest,
    current_user: User = Depends(get_current_user)
):
    """Share deck with another user"""
    # Get deck
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_found"
            )
        )
    
    # Only owner can share
    if deck.owner_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_authorized"
            )
        )
    
    # Cannot share with self
    if payload.user_id == str(current_user.id):
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.cannot_share_with_self"
            )
        )
    
    # Check if user exists
    target_user = await User.get(payload.user_id)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="share.invalid_user"
            )
        )
    
    # Check if already shared
    existing_share = await Share.find_one({
        "deck_id": deck_id,
        "share_with": payload.user_id
    })
    
    if existing_share:
        # Update access level
        existing_share.access_level = payload.access_level
        await existing_share.save()
    else:
        # Create new share
        share = Share(
            deck_id=deck_id,
            owner_id=str(current_user.id),
            share_with=payload.user_id,
            access_level=payload.access_level
        )
        await share.insert()
    
    return api_response(
        request=request,
        success=True,
        message_key="deck.shared",
        data=EmptyData().model_dump()
    )

@router.delete("/{deck_id}/share", response_model=APIResponse[EmptyData])
async def revoke_share(
    request: Request,
    deck_id: str,
    user_id: str = Query(..., description="User ID to revoke share from"),
    current_user: User = Depends(get_current_user)
):
    """Revoke deck sharing"""
    # Get deck
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_found"
            )
        )
    
    # Only owner can revoke
    if deck.owner_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_authorized"
            )
        )
    
    # Find and delete share
    share = await Share.find_one({
        "deck_id": deck_id,
        "share_with": user_id
    })
    
    if not share:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="share.not_found"
            )
        )
    
    await share.delete()
    
    return api_response(
        request=request,
        success=True,
        message_key="deck.share_revoked",
        data=EmptyData().model_dump()
    )

@router.get("/{deck_id}/shares", response_model=APIResponse[ShareListData])
async def get_deck_shares(
    request: Request,
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all shares for a deck"""
    # Get deck
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_found"
            )
        )
    
    # Only owner can view shares
    if deck.owner_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_authorized"
            )
        )
    
    # Get all shares
    shares = await Share.find({"deck_id": deck_id}).to_list()
    
    from app.schemas.share import ShareItem
    shares_data = [
        ShareItem(
            id=str(share.id),
            share_with=share.share_with,
            access_level=share.access_level,
            shared_at=share.shared_at
        )
        for share in shares
    ]
    
    return api_response(
        request=request,
        success=True,
        data=ShareListData(shares=shares_data).model_dump()
    )