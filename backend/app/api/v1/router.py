from fastapi import APIRouter
from app.api.v1.endpoints import auth, decks#, steps, comments, files, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(decks.router, prefix="/decks", tags=["decks"])
# api_router.include_router(steps.router, prefix="/steps", tags=["steps"])
# api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
# api_router.include_router(files.router, prefix="/files", tags=["files"])
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])