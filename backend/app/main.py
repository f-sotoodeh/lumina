from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.deck import Deck
from app.models.step import Step
from app.models.comment import Comment
from app.models.file import FileModel
from app.api.v1.router import api_router
from app.utils.minio_client import create_bucket_if_not_exists

API_PREFIX = "/api/v1"

app = FastAPI(
    title="Lumina API",
    version="1.0.0",
    docs_url=None,
    redoc_url=f"{API_PREFIX}/redoc"
)

MODELS = [User, Deck, Step, Comment, FileModel]

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client.lumina,
        document_models=MODELS
    )
    # create minio bucket if not exists
    await create_bucket_if_not_exists()

app.include_router(api_router, prefix=API_PREFIX)



