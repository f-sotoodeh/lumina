# backend/app/dependencies.py
from fastapi import Depends, HTTPException, status, Cookie
from app.core.security import decode_token
from app.models.user import User
from app.models.deck import Deck
from app.models.share import Share
from typing import Optional, Literal

async def get_current_user(access_token: str = Cookie(None)) -> User:
    """Get current authenticated user (required)"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await User.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_user_optional(access_token: str = Cookie(None)) -> Optional[User]:
    """Get current authenticated user (optional, for public endpoints)"""
    if not access_token:
        return None
    
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        return None
    
    user = await User.get(payload["sub"])
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

AccessLevel = Literal["Editor", "Commenter", "Viewer"]

async def check_deck_access(
    deck_id: str,
    required_level: AccessLevel,
    current_user: User = Depends(get_current_user)
) -> Deck:
    """Check if user has required access level to deck"""
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Owner has full access
    if deck.owner_id == str(current_user.id):
        return deck
    
    # Check share access
    share = await Share.find_one({
        "deck_id": deck_id,
        "share_with": str(current_user.id)
    })
    
    if not share:
        raise HTTPException(status_code=403, detail="Not authorized to access this deck")
    
    # Check access level hierarchy: Editor > Commenter > Viewer
    access_hierarchy = {"Editor": 3, "Commenter": 2, "Viewer": 1}
    
    if access_hierarchy.get(share.access_level, 0) < access_hierarchy.get(required_level, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Requires {required_level} access"
        )
    
    return deck

def check_deck_access_factory(required_level: AccessLevel):
    """Factory function to create access checker with specific level"""
    async def _check_access(
        deck_id: str,
        current_user: User = Depends(get_current_user)
    ) -> Deck:
        return await check_deck_access(deck_id, required_level, current_user)
    return _check_access
