# backend/app/schemas/deck.py
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
import re

def validate_hex_color(value: str) -> str:
    """Validate hex color format: #RRGGBB"""
    if not re.match(r'^#([A-Fa-f0-9]{6})$', value):
        raise ValueError('Invalid hex color format. Must be #RRGGBB')
    return value

def validate_range(value: Optional[int], min_val: int, max_val: int, field_name: str) -> Optional[int]:
    """Validate integer range"""
    if value is not None and (value < min_val or value > max_val):
        raise ValueError(f'{field_name} must be between {min_val} and {max_val}')
    return value

class DeckCreate(BaseModel):
    title: str
    background_color: Optional[str] = "#ffffff"
    data_width: Optional[int] = 1024
    data_height: Optional[int] = 768
    is_public: Optional[bool] = False
    
    @field_validator('background_color')
    @classmethod
    def validate_background_color(cls, v):
        if v:
            return validate_hex_color(v)
        return v
    
    @field_validator('data_width')
    @classmethod
    def validate_data_width(cls, v):
        if v is not None:
            return validate_range(v, 500, 4000, 'data_width')
        return v
    
    @field_validator('data_height')
    @classmethod
    def validate_data_height(cls, v):
        if v is not None:
            return validate_range(v, 500, 4000, 'data_height')
        return v

class DeckUpdate(BaseModel):
    title: Optional[str] = None
    order: Optional[List[str]] = None
    is_public: Optional[bool] = None
    background_color: Optional[str] = None
    data_transition_duration: Optional[int] = None
    data_width: Optional[int] = None
    data_height: Optional[int] = None
    data_max_scale: Optional[int] = None
    data_min_scale: Optional[int] = None
    data_perspective: Optional[int] = None
    data_autoplay: Optional[int] = None
    has_overview: Optional[bool] = None
    overview_x: Optional[float] = None
    overview_y: Optional[float] = None
    overview_z: Optional[float] = None
    overview_scale: Optional[float] = None
    
    @field_validator('background_color')
    @classmethod
    def validate_background_color(cls, v):
        if v:
            return validate_hex_color(v)
        return v
    
    @field_validator('data_width')
    @classmethod
    def validate_data_width(cls, v):
        if v is not None:
            return validate_range(v, 500, 4000, 'data_width')
        return v
    
    @field_validator('data_height')
    @classmethod
    def validate_data_height(cls, v):
        if v is not None:
            return validate_range(v, 500, 4000, 'data_height')
        return v
    
    @field_validator('data_perspective')
    @classmethod
    def validate_data_perspective(cls, v):
        if v is not None:
            return validate_range(v, 100, 5000, 'data_perspective')
        return v

class DeckOut(BaseModel):
    id: str
    title: str
    order: List[str]
    is_public: bool
    preview_url: str
    background_color: str
    data_transition_duration: int
    data_width: int
    data_height: int
    data_max_scale: Optional[int]
    data_min_scale: Optional[int]
    data_perspective: int
    data_autoplay: Optional[int]
    has_overview: bool
    overview_x: float
    overview_y: float
    overview_z: float
    overview_scale: float
    owner_id: str
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Response models for deck endpoints
class DeckCreateData(BaseModel):
    id: str
    preview_url: str

class DeckListItem(BaseModel):
    id: str
    title: str
    is_public: bool
    preview_url: str
    thumbnail_url: Optional[str]
    owner_id: str
    created_at: datetime
    updated_at: datetime

class DeckListData(BaseModel):
    decks: List[DeckListItem]
    total: int
    page: int
    pages: int

class DeckSearchItem(BaseModel):
    id: str
    title: str
    is_public: bool
    preview_url: str
    thumbnail_url: Optional[str]
    owner_id: str

class DeckSearchData(BaseModel):
    decks: List[DeckSearchItem]
    total: int

class DeckCloneData(BaseModel):
    id: str
    title: str

class DeckPreviewStepData(BaseModel):
    id: str
    data_x: float
    data_y: float
    data_z: float
    data_rotate: float
    data_rotate_x: float
    data_rotate_y: float
    data_rotate_z: float
    data_scale: float
    data_transition_duration: int
    data_autoplay: Optional[int]
    is_slide: bool
    inner_html: str
    font_family: Optional[str]

class DeckPreviewDeckData(BaseModel):
    title: str
    background_color: str
    data_width: int
    data_height: int
    data_max_scale: Optional[int]
    data_min_scale: Optional[int]
    data_perspective: int
    data_autoplay: Optional[int]
    has_overview: bool
    overview_x: float
    overview_y: float
    overview_z: float
    overview_scale: float

class DeckPreviewData(BaseModel):
    deck: DeckPreviewDeckData
    steps: List[DeckPreviewStepData]

class DeckFileItem(BaseModel):
    id: str
    original_name: str
    url: str
    thumbnail_url: Optional[str]
    size: int
    file_type: str
    created_at: datetime

class DeckFilesData(BaseModel):
    files: List[DeckFileItem]
    total: int
    page: int
    pages: int

