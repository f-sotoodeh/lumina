# backend/app/api/v1/endpoints/preview.py
from fastapi import APIRouter, HTTPException, Request
from app.models.deck import Deck
from app.models.step import Step
from app.schemas.response import APIResponse
from app.utils.response import api_response
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/{uuid}", response_model=APIResponse)
@limiter.limit("100/hour")
async def get_public_preview(
    request: Request,
    uuid: str
):
    """Get public deck preview (no auth required, rate limited)"""
    # Find deck by preview_url
    deck = await Deck.find_one({"preview_url": uuid})
    if not deck:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_found"
            )
        )
    
    # Check if deck is public
    if not deck.is_public:
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_authorized"
            )
        )
    
    # Get steps
    steps = await Step.find({"deck_id": str(deck.id)}).to_list()
    
    # Sort by deck order
    step_dict = {str(step.id): step for step in steps}
    ordered_steps = [step_dict[step_id] for step_id in deck.order if step_id in step_dict]
    
    steps_data = [
        {
            "id": str(step.id),
            "data_x": step.data_x,
            "data_y": step.data_y,
            "data_z": step.data_z,
            "data_rotate": step.data_rotate,
            "data_rotate_x": step.data_rotate_x,
            "data_rotate_y": step.data_rotate_y,
            "data_rotate_z": step.data_rotate_z,
            "data_scale": step.data_scale,
            "data_transition_duration": step.data_transition_duration,
            "data_autoplay": step.data_autoplay,
            "is_slide": step.is_slide,
            "inner_html": step.inner_html,
            "font_family": step.font_family
        }
        for step in ordered_steps
    ]
    
    return api_response(
        request=request,
        success=True,
        data={
            "deck": {
                "title": deck.title,
                "background_color": deck.background_color,
                "data_width": deck.data_width,
                "data_height": deck.data_height,
                "data_max_scale": deck.data_max_scale,
                "data_min_scale": deck.data_min_scale,
                "data_perspective": deck.data_perspective,
                "data_autoplay": deck.data_autoplay,
                "has_overview": deck.has_overview,
                "overview_x": deck.overview_x,
                "overview_y": deck.overview_y,
                "overview_z": deck.overview_z,
                "overview_scale": deck.overview_scale
            },
            "steps": steps_data
        }
    )

