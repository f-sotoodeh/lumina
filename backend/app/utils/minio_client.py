# backend/app/utils/minio_client.py
from minio import Minio
from app.core.config import settings
import asyncio

async def create_bucket_if_not_exists():
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    bucket_name = settings.MINIO_BUCKET
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created")
        else:
            print(f"Bucket '{bucket_name}' already exists")
    except Exception as e:
        print(f"MinIO error: {e}")