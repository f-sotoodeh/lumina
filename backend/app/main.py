# backend/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.deck import Deck
from app.models.step import Step
from app.models.share import Share
from app.models.comment import Comment
from app.models.file import FileModel
from app.api.v1.router import api_router
from app.utils.minio_client import create_bucket_if_not_exists
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

API_PREFIX = "/api/v1"

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Lumina API",
    version="1.0.0",
    docs_url=None,
    redoc_url=f"{API_PREFIX}/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
cors_origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models list
MODELS = [User, Deck, Step, Comment, FileModel, Share]

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": {
                "en": "Internal server error",
                "ru": "Внутренняя ошибка сервера",
                "hy": "Ներքին սերվերի սխալ"
            },
            "data": None,
            "errors": None
        }
    )

@app.on_event("startup")
async def startup_event():
    """Initialize database and MinIO on startup"""
    # Initialize MongoDB with Beanie
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.lumina,
        document_models=MODELS
    )
    print("✓ MongoDB initialized")
    
    # Create MinIO bucket if not exists
    await create_bucket_if_not_exists()
    print("✓ MinIO bucket initialized")

# Include API router
app.include_router(api_router, prefix=API_PREFIX)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lumina API",
        "version": "1.0.0",
        "docs": f"{API_PREFIX}/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
