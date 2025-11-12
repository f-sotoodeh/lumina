# backend/app/schemas/step.py
from pydantic import BaseModel
from typing import Optional, List

class StepCreate(BaseModel):
    data_x: Optional[float] = 0.0
    data_y: Optional[float] = 0.0
    data_z: Optional[float] = 0.0
    data_rotate: Optional[float] = 0.0
    data_rotate_x: Optional[float] = 0.0
    data_rotate_y: Optional[float] = 0.0
    data_rotate_z: Optional[float] = 0.0
    data_scale: Optional[float] = 1.0
    data_transition_duration: Optional[int] = 1000
    data_autoplay: Optional[int] = None
    is_slide: Optional[bool] = True
    inner_html: Optional[str] = "<h1>New Slide</h1>"
    notes: Optional[str] = ""
    font_family: Optional[str] = None

class StepUpdateSettings(BaseModel):
    data_x: Optional[float] = None
    data_y: Optional[float] = None
    data_z: Optional[float] = None
    data_rotate: Optional[float] = None
    data_rotate_x: Optional[float] = None
    data_rotate_y: Optional[float] = None
    data_rotate_z: Optional[float] = None
    data_scale: Optional[float] = None
    data_transition_duration: Optional[int] = None
    data_autoplay: Optional[int] = None
    is_slide: Optional[bool] = None

class StepUpdateData(BaseModel):
    inner_html: Optional[str] = None
    notes: Optional[str] = None
    font_family: Optional[str] = None

class StepOut(BaseModel):
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
    notes: str
    font_family: Optional[str]
    user_id: str
    deck_id: str

    class Config:
        from_attributes = True

# Response models for step endpoints
class StepListData(BaseModel):
    steps: List[StepOut]
    total: int
    page: int
    pages: int

class StepCreateData(BaseModel):
    id: str

class StepDuplicateData(BaseModel):
    id: str
