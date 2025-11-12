# backend/app/schemas/common.py
from pydantic import BaseModel

class EmptyData(BaseModel):
    """Empty response data for endpoints that don't return data"""
    pass

