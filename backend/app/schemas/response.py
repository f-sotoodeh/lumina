# backend/app/schemas/response.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Dict, List, Any, Optional

T = TypeVar("T")

class MessageDict(BaseModel):
    en: str
    ru: str
    hy: str

class ErrorItem(BaseModel):
    field: Optional[str] = None
    message: MessageDict

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[MessageDict] = None
    errors: Optional[List[ErrorItem]] = None