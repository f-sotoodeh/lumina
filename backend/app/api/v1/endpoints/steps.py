# backend/app/api/v1/endpoints/steps.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.step import Step
from app.models.deck import Deck
from app.models.user import User
from app.schemas.step import (
    StepCreate, StepUpdateSettings, StepUpdateData, StepOut,
    StepListData, StepCreateData, StepDuplicateData
)
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user, check_deck_access
from pydantic import BaseModel
from datetime import datetime
from pytz import UTC
from typing import List
import bleach

router = APIRouter()

# Allowed HTML tags and attributes (from mindmap)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'span', 'div',
    'img', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre'
]

ALLOWED_ATTRS = {
    '*': ['style', 'class'],
    'img': ['src', 'alt', 'width', 'height'],
    'a': ['href', 'target', 'rel']
}

def sanitize_html(html: str) -> str:
    """Sanitize HTML using bleach"""
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)

def clamp_position(value: float) -> float:
    """Clamp position values to valid range (-50000 to 50000)"""
    import math
    if math.isnan(value):
        return 0.0
    return max(-50000.0, min(50000.0, value))

class ReorderStepsRequest(BaseModel):
    step_ids: List[str]

@router.get("/decks/{deck_id}", response_model=APIResponse[StepListData])
async def get_deck_steps(
    request: Request,
    deck_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get all steps of a deck"""
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
    
    # Get steps in order
    steps = await Step.find({"deck_id": deck_id}).skip(offset).limit(limit).to_list()
    total = await Step.find({"deck_id": deck_id}).count()
    
    # Sort by deck.order
    step_dict = {str(step.id): step for step in steps}
    ordered_steps = []
    for step_id in deck.order:
        if step_id in step_dict:
            ordered_steps.append(step_dict[step_id])
    
    # Add any steps not in order
    for step in steps:
        if str(step.id) not in deck.order:
            ordered_steps.append(step)
    
    steps_data = [StepOut.model_validate(step) for step in ordered_steps]
    
    pages = (total + limit - 1) // limit
    page = offset // limit + 1
    
    return api_response(
        request=request,
        success=True,
        data=StepListData(
            steps=steps_data,
            total=total,
            page=page,
            pages=pages
        ).model_dump()
    )

@router.post("/decks/{deck_id}", response_model=APIResponse[StepCreateData])
async def create_step(
    request: Request,
    deck_id: str,
    payload: StepCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new step in deck"""
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
    
    # Check access (Editor required)
    if deck.owner_id != str(current_user.id):
        # Check share access
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Sanitize HTML
    sanitized_html = sanitize_html(payload.inner_html or "<h1>New Slide</h1>")
    
    # Clamp positions
    data_x = clamp_position(payload.data_x or 0.0)
    data_y = clamp_position(payload.data_y or 0.0)
    data_z = clamp_position(payload.data_z or 0.0)
    
    # Create step
    step = Step(
        user_id=str(current_user.id),
        deck_id=deck_id,
        data_x=data_x,
        data_y=data_y,
        data_z=data_z,
        data_rotate=payload.data_rotate or 0.0,
        data_rotate_x=payload.data_rotate_x or 0.0,
        data_rotate_y=payload.data_rotate_y or 0.0,
        data_rotate_z=payload.data_rotate_z or 0.0,
        data_scale=payload.data_scale or 1.0,
        data_transition_duration=payload.data_transition_duration or 1000,
        data_autoplay=payload.data_autoplay,
        is_slide=payload.is_slide if payload.is_slide is not None else True,
        inner_html=sanitized_html,
        notes=payload.notes or "",
        font_family=payload.font_family
    )
    await step.insert()
    
    # Append to deck order
    deck.order.append(str(step.id))
    deck.updated_at = datetime.now(UTC)
    await deck.save()
    
    # Generate thumbnail if first step
    if len(deck.order) == 1:
        from app.utils.deck_thumbnail import generate_deck_thumbnail
        await generate_deck_thumbnail(deck_id)
    else:
        # Schedule thumbnail regeneration with debounce
        from app.utils.deck_thumbnail import schedule_thumbnail_regeneration
        await schedule_thumbnail_regeneration(deck_id, delay=2.0)
    
    return api_response(
        request=request,
        success=True,
        message_key="step.created",
        data=StepCreateData(id=str(step.id)).model_dump()
    )

@router.patch("/decks/{deck_id}/reorder", response_model=APIResponse[EmptyData])
async def reorder_steps(
    request: Request,
    deck_id: str,
    payload: ReorderStepsRequest,
    current_user: User = Depends(get_current_user)
):
    """Reorder steps in deck"""
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
    
    # Check access (Editor required)
    if deck.owner_id != str(current_user.id):
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Update order
    deck.order = payload.step_ids
    deck.updated_at = datetime.now(UTC)
    await deck.save()
    
    # Schedule thumbnail regeneration with debounce
    from app.utils.deck_thumbnail import schedule_thumbnail_regeneration
    await schedule_thumbnail_regeneration(deck_id, delay=2.0)
    
    return api_response(
        request=request,
        success=True,
        message_key="step.reordered",
        data=EmptyData().model_dump()
    )

@router.put("/{step_id}/settings", response_model=APIResponse[StepOut])
async def update_step_settings(
    request: Request,
    step_id: str,
    payload: StepUpdateSettings,
    current_user: User = Depends(get_current_user)
):
    """Update step position and settings"""
    step = await Step.get(step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="step.not_found"
            )
        )
    
    # Check access (Editor required)
    deck = await Deck.get(step.deck_id)
    if deck.owner_id != str(current_user.id):
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": step.deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Update fields with clamping for positions
    if payload.data_x is not None:
        step.data_x = clamp_position(payload.data_x)
    if payload.data_y is not None:
        step.data_y = clamp_position(payload.data_y)
    if payload.data_z is not None:
        step.data_z = clamp_position(payload.data_z)
    if payload.data_rotate is not None:
        step.data_rotate = payload.data_rotate
    if payload.data_rotate_x is not None:
        step.data_rotate_x = payload.data_rotate_x
    if payload.data_rotate_y is not None:
        step.data_rotate_y = payload.data_rotate_y
    if payload.data_rotate_z is not None:
        step.data_rotate_z = payload.data_rotate_z
    if payload.data_scale is not None:
        step.data_scale = payload.data_scale
    if payload.data_transition_duration is not None:
        step.data_transition_duration = payload.data_transition_duration
    if payload.data_autoplay is not None:
        step.data_autoplay = payload.data_autoplay
    if payload.is_slide is not None:
        step.is_slide = payload.is_slide
    
    await step.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="step.updated",
        data=StepOut.model_validate(step).model_dump()
    )

@router.put("/{step_id}/data", response_model=APIResponse[StepOut])
async def update_step_data(
    request: Request,
    step_id: str,
    payload: StepUpdateData,
    current_user: User = Depends(get_current_user)
):
    """Update step content data"""
    step = await Step.get(step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="step.not_found"
            )
        )
    
    # Check access (Editor required)
    deck = await Deck.get(step.deck_id)
    if deck.owner_id != str(current_user.id):
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": step.deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Update fields with sanitization for HTML
    if payload.inner_html is not None:
        step.inner_html = sanitize_html(payload.inner_html)
    if payload.notes is not None:
        step.notes = payload.notes
    if payload.font_family is not None:
        step.font_family = payload.font_family
    
    await step.save()
    
    # Schedule thumbnail regeneration with debounce
    from app.utils.deck_thumbnail import schedule_thumbnail_regeneration
    await schedule_thumbnail_regeneration(step.deck_id, delay=2.0)
    
    return api_response(
        request=request,
        success=True,
        message_key="step.updated",
        data=StepOut.model_validate(step).model_dump()
    )

@router.delete("/{step_id}", response_model=APIResponse[EmptyData])
async def delete_step(
    request: Request,
    step_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a step"""
    step = await Step.get(step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="step.not_found"
            )
        )
    
    # Check access (Editor required)
    deck = await Deck.get(step.deck_id)
    if deck.owner_id != str(current_user.id):
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": step.deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Remove from deck order
    if str(step.id) in deck.order:
        deck.order.remove(str(step.id))
        deck.updated_at = datetime.now(UTC)
        await deck.save()
        
        # Regenerate thumbnail if steps remain
        if len(deck.order) > 0:
            from app.utils.deck_thumbnail import schedule_thumbnail_regeneration
            await schedule_thumbnail_regeneration(step.deck_id, delay=2.0)
        else:
            # Clear thumbnail if no steps
            deck.thumbnail_url = None
            await deck.save()
    
    # Delete step
    await step.delete()
    
    return api_response(
        request=request,
        success=True,
        message_key="step.deleted",
        data=EmptyData().model_dump()
    )

@router.post("/{step_id}/duplicate", response_model=APIResponse[StepDuplicateData])
async def duplicate_step(
    request: Request,
    step_id: str,
    current_user: User = Depends(get_current_user)
):
    """Duplicate a step"""
    step = await Step.get(step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="step.not_found"
            )
        )
    
    # Check access (Editor required)
    deck = await Deck.get(step.deck_id)
    if deck.owner_id != str(current_user.id):
        from app.models.share import Share
        share = await Share.find_one({
            "deck_id": step.deck_id,
            "share_with": str(current_user.id)
        })
        if not share or share.access_level != "Editor":
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="step.not_authorized"
                )
            )
    
    # Create duplicate
    new_step = Step(
        user_id=str(current_user.id),
        deck_id=step.deck_id,
        data_x=step.data_x,
        data_y=step.data_y,
        data_z=step.data_z,
        data_rotate=step.data_rotate,
        data_rotate_x=step.data_rotate_x,
        data_rotate_y=step.data_rotate_y,
        data_rotate_z=step.data_rotate_z,
        data_scale=step.data_scale,
        data_transition_duration=step.data_transition_duration,
        data_autoplay=step.data_autoplay,
        is_slide=step.is_slide,
        inner_html=step.inner_html,
        notes=step.notes,
        font_family=step.font_family
    )
    await new_step.insert()
    
    # Append to deck order
    deck.order.append(str(new_step.id))
    deck.updated_at = datetime.now(UTC)
    await deck.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="step.duplicated",
        data=StepDuplicateData(id=str(new_step.id)).model_dump()
    )

