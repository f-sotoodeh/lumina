# backend/app/schemas/comment.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

class CommentOut(BaseModel):
    id: str
    user_id: str
    text: str
    is_edited: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Response models for comment endpoints
class CommentCountData(BaseModel):
    count: int

class CommentListData(BaseModel):
    comments: List[CommentOut]
    total: int

class CommentCreateData(BaseModel):
    id: str
    text: str
    created_at: datetime

class CommentUpdateData(BaseModel):
    id: str
    text: str
    is_edited: bool

