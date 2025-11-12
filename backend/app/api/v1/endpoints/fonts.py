# backend/app/api/v1/endpoints/fonts.py
from fastapi import APIRouter, Request
from app.schemas.font import FontListData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from pathlib import Path
import json

router = APIRouter()

# Load fonts from JSON file on module import
FONTS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "fonts.json"

def load_fonts():
    """Load fonts from JSON file"""
    try:
        with open(FONTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading fonts: {e}")
        return []

FONTS = load_fonts()

@router.get("/", response_model=APIResponse[FontListData])
async def get_fonts(request: Request):
    """Get list of available Google Fonts (public endpoint)"""
    from app.schemas.font import FontItem
    fonts_data = [
        FontItem(family=font.get("family", ""), category=font.get("category"))
        for font in FONTS
    ]
    return api_response(
        request=request,
        success=True,
        message_key="fonts.loaded",
        data=FontListData(fonts=fonts_data).model_dump()
    )

