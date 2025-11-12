# backend/app/utils/minio_client.py
from minio import Minio
from app.core.config import settings
from datetime import timedelta
from io import BytesIO
from typing import Optional
import uuid

def get_minio_client() -> Minio:
    """Get MinIO client instance"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )

async def create_bucket_if_not_exists():
    """Create bucket if it doesn't exist"""
    client = get_minio_client()
    bucket_name = settings.MINIO_BUCKET
    
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created")
        else:
            print(f"Bucket '{bucket_name}' already exists")
    except Exception as e:
        print(f"MinIO error: {e}")

def upload_file(
    file_data: bytes,
    object_name: str,
    content_type: str = "application/octet-stream",
    metadata: Optional[dict] = None
) -> str:
    """
    Upload file to MinIO
    Returns: object_name
    """
    client = get_minio_client()
    bucket_name = settings.MINIO_BUCKET
    
    file_stream = BytesIO(file_data)
    file_size = len(file_data)
    
    client.put_object(
        bucket_name,
        object_name,
        file_stream,
        file_size,
        content_type=content_type,
        metadata=metadata or {}
    )
    
    return object_name

def delete_file(object_name: str) -> bool:
    """Delete file from MinIO"""
    try:
        client = get_minio_client()
        bucket_name = settings.MINIO_BUCKET
        client.remove_object(bucket_name, object_name)
        return True
    except Exception as e:
        print(f"Error deleting file {object_name}: {e}")
        return False

def get_presigned_url(object_name: str, expiry_days: int = 7) -> str:
    """Get presigned URL for file (default 7 days expiry)"""
    client = get_minio_client()
    bucket_name = settings.MINIO_BUCKET
    
    try:
        url = client.presigned_get_object(
            bucket_name,
            object_name,
            expires=timedelta(days=expiry_days)
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL for {object_name}: {e}")
        return ""

def upload_avatar(user_id: str, file_data: bytes, content_type: str) -> tuple[str, str]:
    """
    Upload user avatar (original and thumbnail)
    Returns: (original_path, thumbnail_path)
    """
    from app.utils.thumbnail import create_thumbnail
    
    # Upload original
    original_path = f"avatars/{user_id}/original"
    upload_file(file_data, original_path, content_type)
    
    # Create and upload thumbnail (64x64)
    thumbnail_data = create_thumbnail(file_data, size=(64, 64), format="JPEG")
    thumbnail_path = f"avatars/{user_id}/thumb_64.jpg"
    upload_file(thumbnail_data, thumbnail_path, "image/jpeg")
    
    return (original_path, thumbnail_path)

def delete_avatar(user_id: str) -> bool:
    """Delete user avatar (original and thumbnail)"""
    try:
        delete_file(f"avatars/{user_id}/original")
        delete_file(f"avatars/{user_id}/thumb_64.jpg")
        return True
    except Exception as e:
        print(f"Error deleting avatar for user {user_id}: {e}")
        return False

def upload_deck_file(
    deck_id: str,
    file_data: bytes,
    original_filename: str,
    content_type: str
) -> tuple[str, Optional[str], str]:
    """
    Upload deck file with thumbnail if image
    Returns: (minio_id, thumbnail_minio_id, object_name)
    """
    from app.utils.thumbnail import create_thumbnail, is_image_type
    
    # Generate unique filename
    extension = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else ''
    minio_id = str(uuid.uuid4())
    object_name = f"decks/{deck_id}/{minio_id}.{extension}" if extension else f"decks/{deck_id}/{minio_id}"
    
    # Upload original file
    upload_file(file_data, object_name, content_type)
    
    # Create thumbnail if image
    thumbnail_object_name = None
    if is_image_type(content_type):
        try:
            thumbnail_data = create_thumbnail(file_data, size=(200, 200), format="JPEG")
            thumbnail_object_name = f"decks/{deck_id}/thumb_{minio_id}.jpg"
            upload_file(thumbnail_data, thumbnail_object_name, "image/jpeg")
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
    
    return (minio_id, thumbnail_object_name, object_name)

def delete_deck_file(object_name: str, thumbnail_object_name: Optional[str] = None) -> bool:
    """Delete deck file and its thumbnail"""
    success = delete_file(object_name)
    if thumbnail_object_name:
        delete_file(thumbnail_object_name)
    return success
