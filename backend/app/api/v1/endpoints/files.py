# backend/app/api/v1/endpoints/files.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query, File, UploadFile
from app.models.file import FileModel
from app.models.deck import Deck
from app.models.user import User
from app.schemas.file import (
    FileOut, FileUploadResponse,
    FileQuotaData, FileGetData, FileUploadListData
)
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user
from app.utils.minio_client import upload_deck_file, delete_deck_file, get_presigned_url
from typing import List

router = APIRouter()

# File quota: 100MB per user
QUOTA_MB = 100
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file
ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml', 'image/gif']

async def get_user_storage_usage(user_id: str) -> float:
    """Get user's total storage usage in MB"""
    files = await FileModel.find({"user_id": user_id}).to_list()
    total_bytes = sum(file.size for file in files)
    return total_bytes / (1024 * 1024)  # Convert to MB

@router.get("/quota", response_model=APIResponse[FileQuotaData])
async def get_storage_quota(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get user's storage quota and usage"""
    used = await get_user_storage_usage(str(current_user.id))
    
    return api_response(
        request=request,
        success=True,
        data=FileQuotaData(
            used=round(used, 2),
            limit=QUOTA_MB,
            unit="MB"
        ).model_dump()
    )

@router.get("/{file_id}", response_model=APIResponse[FileGetData])
async def get_file(
    request: Request,
    file_id: str,
    thumbnail: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get file by ID"""
    file = await FileModel.get(file_id)
    if not file:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.not_found"
            )
        )
    
    # Regenerate presigned URL
    url = get_presigned_url(file.minio_id, expiry_days=7)
    thumbnail_url = None
    if file.thumbnail_url:
        thumbnail_minio_id = f"decks/{file.deck_id}/thumb_{file.minio_id}.jpg"
        thumbnail_url = get_presigned_url(thumbnail_minio_id, expiry_days=7)
    
    return api_response(
        request=request,
        success=True,
        data=FileGetData(
            id=str(file.id),
            original_name=file.original_name,
            url=url if not thumbnail else (thumbnail_url or url),
            thumbnail_url=thumbnail_url,
            size=file.size,
            file_type=file.file_type
        ).model_dump()
    )

@router.post("/upload", response_model=APIResponse[FileUploadListData])
async def upload_files(
    request: Request,
    deck_id: str = Query(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload files to a deck"""
    # Check deck access
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
    
    # Check user quota
    used_mb = await get_user_storage_usage(str(current_user.id))
    
    uploaded_files = []
    
    for file in files:
        # Validate file type
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="file.invalid_file_type",
                    errors=[{"field": "file", "message": "file.invalid_file_type"}]
                )
            )
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="file.file_too_large"
                )
            )
        
        # Check quota
        file_size_mb = file_size / (1024 * 1024)
        if used_mb + file_size_mb > QUOTA_MB:
            raise HTTPException(
                status_code=413,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="file.quota_exceeded"
                )
            )
        
        # Upload to MinIO
        minio_id, thumbnail_object_name, object_name = upload_deck_file(
            deck_id,
            file_data,
            file.filename,
            file.content_type
        )
        
        # Get presigned URLs
        url = get_presigned_url(object_name, expiry_days=7)
        thumbnail_url = None
        if thumbnail_object_name:
            thumbnail_url = get_presigned_url(thumbnail_object_name, expiry_days=7)
        
        # Save to database
        file_model = FileModel(
            user_id=str(current_user.id),
            deck_id=deck_id,
            original_name=file.filename,
            minio_id=object_name,
            url=url,
            thumbnail_url=thumbnail_object_name,
            size=file_size,
            file_type=file.content_type
        )
        await file_model.insert()
        
        uploaded_files.append(FileUploadResponse(
            file_id=str(file_model.id),
            url=url,
            thumbnail_url=thumbnail_url,
            original_name=file.filename
        ))
        
        # Update used quota
        used_mb += file_size_mb
    
    return api_response(
        request=request,
        success=True,
        message_key="file.uploaded",
        data=FileUploadListData(files=uploaded_files).model_dump()
    )

@router.delete("/{file_id}", response_model=APIResponse[EmptyData])
async def delete_file(
    request: Request,
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file"""
    file = await FileModel.get(file_id)
    if not file:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.not_found"
            )
        )
    
    # Only owner can delete
    if file.user_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="file.not_authorized"
            )
        )
    
    # Delete from MinIO
    delete_deck_file(file.minio_id, file.thumbnail_url)
    
    # Delete from database
    await file.delete()
    
    return api_response(
        request=request,
        success=True,
        message_key="file.deleted",
        data=EmptyData().model_dump()
    )

