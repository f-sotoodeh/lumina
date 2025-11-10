from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://mongo:27017"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "lumina"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        load_dotenv()
        return Settings()

settings = get_settings()
