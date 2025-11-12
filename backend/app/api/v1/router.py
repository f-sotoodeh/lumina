# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, decks, steps, comments, files, 
    admin, shares, user, fonts, preview
)

api_router = APIRouter()

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User endpoints
api_router.include_router(user.router, prefix="/users", tags=["users"])

# Deck endpoints
api_router.include_router(decks.router, prefix="/decks", tags=["decks"])

# Step endpoints
api_router.include_router(steps.router, prefix="/steps", tags=["steps"])

# Comment endpoints
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])

# File endpoints
api_router.include_router(files.router, prefix="/files", tags=["files"])

# Share endpoints (mounted under /decks to match mindmap: /api/v1/decks/{id}/share)
api_router.include_router(shares.router, prefix="/decks", tags=["shares"])

# Font endpoints
api_router.include_router(fonts.router, prefix="/fonts", tags=["fonts"])

# Admin endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Public preview endpoint
api_router.include_router(preview.router, prefix="/preview", tags=["preview"])
