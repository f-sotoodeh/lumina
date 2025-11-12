# backend/app/api/v1/endpoints/decks.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.deck import Deck
from app.models.step import Step
from app.models.share import Share
from app.models.user import User
from app.models.file import FileModel
from app.utils.minio_client import get_presigned_url
from app.schemas.deck import (
    DeckCreate, DeckUpdate, DeckOut,
    DeckCreateData, DeckListData, DeckListItem,
    DeckSearchData, DeckSearchItem,
    DeckCloneData, DeckPreviewData, DeckPreviewDeckData, DeckPreviewStepData,
    DeckFilesData, DeckFileItem
)
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user, get_current_user_optional
from datetime import datetime
from pytz import UTC
from uuid import uuid4
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError

router = APIRouter()

def handle_validation_error(e: ValidationError, request: Request):
    """Convert Pydantic validation errors to API response format"""
    errors = []
    for error in e.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        
        # Map error messages to message keys
        if "hex color" in msg.lower():
            message_key = "validation.invalid_hex_color"
        elif "between" in msg.lower() or "range" in msg.lower():
            message_key = "validation.value_out_of_range"
        else:
            message_key = "validation.field_required"
        
        errors.append({
            "field": field,
            "message": message_key
        })
    
    raise HTTPException(
        status_code=400,
        detail=api_response(
            request=request,
            success=False,
            message_key="validation.field_required",
            errors=errors
        )
    )

@router.post("/", response_model=APIResponse[DeckCreateData])
async def create_deck(
    request: Request,
    payload: DeckCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new deck"""
    try:
        deck = Deck(
            title=payload.title,
            background_color=payload.background_color or "#ffffff",
            data_width=payload.data_width or 1024,
            data_height=payload.data_height or 768,
            is_public=payload.is_public or False,
            owner_id=str(current_user.id),
            preview_url=str(uuid4())
        )
        await deck.insert()
        
        return api_response(
            request=request,
            success=True,
            message_key="deck.created",
            data=DeckCreateData(id=str(deck.id), preview_url=deck.preview_url).model_dump()
        )
    except ValidationError as e:
        handle_validation_error(e, request)

@router.get("/", response_model=APIResponse[DeckListData])
async def get_decks(
    request: Request,
    mine: bool = Query(False),
    shared_with_me: bool = Query(False),
    owner_name: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get decks with filters"""
    query = {}
    
    if mine:
        query["owner_id"] = str(current_user.id)
    
    if shared_with_me:
        # Get shared deck IDs
        shares = await Share.find({"share_with": str(current_user.id)}).to_list()
        deck_ids = [share.deck_id for share in shares]
        query["_id"] = {"$in": deck_ids}
    
    if owner_name:
        # Find users by name
        users = await User.find({
            "$or": [
                {"first_name": {"$regex": owner_name, "$options": "i"}},
                {"last_name": {"$regex": owner_name, "$options": "i"}}
            ]
        }).to_list()
        user_ids = [str(user.id) for user in users]
        query["owner_id"] = {"$in": user_ids}
    
    decks = await Deck.find(query).skip(offset).limit(limit).sort("-created_at").to_list()
    total = await Deck.find(query).count()
    
    decks_data = [
        DeckListItem(
            id=str(deck.id),
            title=deck.title,
            is_public=deck.is_public,
            preview_url=deck.preview_url,
            thumbnail_url=deck.thumbnail_url,
            owner_id=deck.owner_id,
            created_at=deck.created_at,
            updated_at=deck.updated_at
        )
        for deck in decks
    ]
    
    pages = (total + limit - 1) // limit
    page = offset // limit + 1
    
    return api_response(
        request=request,
        success=True,
        data=DeckListData(
            decks=decks_data,
            total=total,
            page=page,
            pages=pages
        ).model_dump()
    )

@router.get("/search", response_model=APIResponse[DeckSearchData])
async def search_decks(
    request: Request,
    q: str = Query(..., min_length=1),
    sort: str = Query("relevance", regex="^(relevance|title_asc|title_desc|created_desc|updated_desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User | None = Depends(get_current_user_optional)
):
    """Search decks by title (JWT optional, public decks visible without JWT)"""
    # Text search
    query = {"$text": {"$search": q}}
    
    # If no user, only show public decks
    if not current_user:
        query["is_public"] = True
    else:
        # If user exists, show: user's decks + public decks + shared decks
        shared_decks = await Share.find({"share_with": str(current_user.id)}).to_list()
        shared_deck_ids = [share.deck_id for share in shared_decks]
        
        query = {
            "$or": [
                {"$text": {"$search": q}, "owner_id": str(current_user.id)},
                {"$text": {"$search": q}, "is_public": True},
                {"$text": {"$search": q}, "_id": {"$in": shared_deck_ids}}
            ]
        }
    
    # Sort options
    sort_options = {
        "relevance": [("score", {"$meta": "textScore"})],
        "title_asc": [("title", 1)],
        "title_desc": [("title", -1)],
        "created_desc": [("created_at", -1)],
        "updated_desc": [("updated_at", -1)]
    }
    
    sort_by = sort_options.get(sort, [("score", {"$meta": "textScore"})])
    
    # Execute search
    if sort == "relevance":
        decks = await Deck.find(query, projection={"score": {"$meta": "textScore"}}).skip(offset).limit(limit).sort(*sort_by).to_list()
    else:
        decks = await Deck.find(query).skip(offset).limit(limit).sort(*sort_by).to_list()
    
    total = await Deck.find(query).count()
    
    decks_data = [
        DeckSearchItem(
            id=str(deck.id),
            title=deck.title,
            is_public=deck.is_public,
            preview_url=deck.preview_url,
            thumbnail_url=deck.thumbnail_url,
            owner_id=deck.owner_id
        )
        for deck in decks
    ]
    
    return api_response(
        request=request,
        success=True,
        data=DeckSearchData(decks=decks_data, total=total).model_dump()
    )

@router.get("/{deck_id}", response_model=APIResponse[DeckOut])
async def get_deck(
    request: Request,
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get deck by ID"""
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
    
    # Check access
    if deck.owner_id != str(current_user.id):
        share = await Share.find_one({
            "deck_id": deck_id,
            "share_with": str(current_user.id)
        })
        if not share:
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="deck.not_authorized"
                )
            )
    
    return api_response(
        request=request,
        success=True,
        data=DeckOut.model_validate(deck).model_dump()
    )

@router.put("/{deck_id}", response_model=APIResponse[DeckOut])
async def update_deck(
    request: Request,
    deck_id: str,
    payload: DeckUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update deck"""
    try:
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
        
        # Only owner can update
        if deck.owner_id != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="deck.not_authorized"
                )
            )
        
        # Update fields
        if payload.title is not None:
            deck.title = payload.title
        if payload.order is not None:
            deck.order = payload.order
        if payload.is_public is not None:
            deck.is_public = payload.is_public
        if payload.background_color is not None:
            deck.background_color = payload.background_color
        if payload.data_transition_duration is not None:
            deck.data_transition_duration = payload.data_transition_duration
        if payload.data_width is not None:
            deck.data_width = payload.data_width
        if payload.data_height is not None:
            deck.data_height = payload.data_height
        if payload.data_max_scale is not None:
            deck.data_max_scale = payload.data_max_scale
        if payload.data_min_scale is not None:
            deck.data_min_scale = payload.data_min_scale
        if payload.data_perspective is not None:
            deck.data_perspective = payload.data_perspective
        if payload.data_autoplay is not None:
            deck.data_autoplay = payload.data_autoplay
        if payload.has_overview is not None:
            deck.has_overview = payload.has_overview
        if payload.overview_x is not None:
            deck.overview_x = payload.overview_x
        if payload.overview_y is not None:
            deck.overview_y = payload.overview_y
        if payload.overview_z is not None:
            deck.overview_z = payload.overview_z
        if payload.overview_scale is not None:
            deck.overview_scale = payload.overview_scale
        
        deck.updated_at = datetime.now(UTC)
        await deck.save()
        
        return api_response(
            request=request,
            success=True,
            message_key="deck.updated",
            data=DeckOut.model_validate(deck).model_dump()
        )
    except ValidationError as e:
        handle_validation_error(e, request)

@router.delete("/{deck_id}", response_model=APIResponse[EmptyData])
async def delete_deck(
    request: Request,
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete deck (cascade delete steps, comments, files, shares)"""
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
    
    # Only owner can delete
    if deck.owner_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="deck.not_authorized"
            )
        )
    
    # Cascade delete steps
    await Step.find({"deck_id": deck_id}).delete()
    
    # Cascade delete comments
    from app.models.comment import Comment
    await Comment.find({"deck_id": deck_id}).delete()
    
    # Cascade delete files
    from app.models.file import FileModel
    files = await FileModel.find({"deck_id": deck_id}).to_list()
    for file in files:
        from app.utils.minio_client import delete_deck_file
        delete_deck_file(file.minio_id, file.thumbnail_url)
        await file.delete()
    
    # Cascade delete shares
    await Share.find({"deck_id": deck_id}).delete()
    
    # Delete deck
    await deck.delete()
    
    return api_response(
        request=request,
        success=True,
        message_key="deck.deleted",
        data=EmptyData().model_dump()
    )

@router.post("/{deck_id}/clone", response_model=APIResponse[DeckCloneData])
async def clone_deck(
    request: Request,
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """Clone a deck with all steps"""
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
    
    # Create new deck
    new_deck = Deck(
        title=f"{deck.title} (Copy)",
        order=[],
        is_public=False,
        preview_url=str(uuid4()),
        background_color=deck.background_color,
        data_transition_duration=deck.data_transition_duration,
        data_width=deck.data_width,
        data_height=deck.data_height,
        data_max_scale=deck.data_max_scale,
        data_min_scale=deck.data_min_scale,
        data_perspective=deck.data_perspective,
        data_autoplay=deck.data_autoplay,
        has_overview=deck.has_overview,
        overview_x=deck.overview_x,
        overview_y=deck.overview_y,
        overview_z=deck.overview_z,
        overview_scale=deck.overview_scale,
        owner_id=str(current_user.id)
    )
    await new_deck.insert()
    
    # Clone steps
    steps = await Step.find({"deck_id": deck_id}).to_list()
    step_id_map = {}  # Old ID -> New ID mapping
    
    for step in steps:
        new_step = Step(
            user_id=str(current_user.id),
            deck_id=str(new_deck.id),
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
        step_id_map[str(step.id)] = str(new_step.id)
    
    # Update deck order with new step IDs
    new_deck.order = [step_id_map.get(old_id, old_id) for old_id in deck.order if old_id in step_id_map]
    await new_deck.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="deck.cloned",
        data=DeckCloneData(id=str(new_deck.id), title=new_deck.title).model_dump()
    )

@router.get("/{deck_id}/export")
async def export_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user)
):
    """Export deck to HTML"""
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Check access
    if deck.owner_id != str(current_user.id):
        share = await Share.find_one({
            "deck_id": deck_id,
            "share_with": str(current_user.id)
        })
        if not share:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Generate HTML
    from app.utils.export import export_deck_to_html
    html = await export_deck_to_html(deck_id)
    
    return HTMLResponse(content=html, headers={
        "Content-Disposition": f'attachment; filename="{deck.title}.html"'
    })

@router.get("/{deck_id}/preview", response_model=APIResponse[DeckPreviewData])
async def preview_deck(
    request: Request,
    deck_id: str,
    current_user: User | None = Depends(get_current_user_optional)
):
    """Get deck preview data for impress.js (JWT optional for public decks)"""
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
    
    # Check access
    if not current_user:
        # No user, only allow public decks
        if not deck.is_public:
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="deck.not_authorized"
                )
            )
    else:
        # User exists, check ownership or share
        if deck.owner_id != str(current_user.id):
            share = await Share.find_one({
                "deck_id": deck_id,
                "share_with": str(current_user.id)
            })
            if not share and not deck.is_public:
                raise HTTPException(
                    status_code=403,
                    detail=api_response(
                        request=request,
                        success=False,
                        message_key="deck.not_authorized"
                    )
                )
    
    # Get steps
    steps = await Step.find({"deck_id": deck_id}).to_list()
    
    # Sort by deck order
    step_dict = {str(step.id): step for step in steps}
    ordered_steps = [step_dict[step_id] for step_id in deck.order if step_id in step_dict]
    
    steps_data = [
        DeckPreviewStepData(
            id=str(step.id),
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
            font_family=step.font_family
        )
        for step in ordered_steps
    ]
    
    deck_data = DeckPreviewDeckData(
        title=deck.title,
        background_color=deck.background_color,
        data_width=deck.data_width,
        data_height=deck.data_height,
        data_max_scale=deck.data_max_scale,
        data_min_scale=deck.data_min_scale,
        data_perspective=deck.data_perspective,
        data_autoplay=deck.data_autoplay,
        has_overview=deck.has_overview,
        overview_x=deck.overview_x,
        overview_y=deck.overview_y,
        overview_z=deck.overview_z,
        overview_scale=deck.overview_scale
    )
    
    return api_response(
        request=request,
        success=True,
        data=DeckPreviewData(deck=deck_data, steps=steps_data).model_dump()
    )

@router.get("/{deck_id}/thumbnail/fallback")
async def get_deck_thumbnail_fallback(
    deck_id: str
):
    """Get SVG thumbnail fallback for deck"""
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Get background color or default
    bg_color = deck.background_color or "#6366f1"
    
    # Generate SVG
    svg = f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{bg_color};stop-opacity:0.7" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" fill="url(#grad)"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="18" fill="white" text-anchor="middle" dominant-baseline="central" font-weight="bold">{deck.title}</text>
</svg>'''
    
    return Response(content=svg, media_type="image/svg+xml")

@router.get("/{deck_id}/files", response_model=APIResponse[DeckFilesData])
async def get_deck_files(
    request: Request,
    deck_id: str,
    thumbnail: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get all files for a deck"""
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
    
    # Check access (Viewer or higher)
    if deck.owner_id != str(current_user.id):
        share = await Share.find_one({
            "deck_id": deck_id,
            "share_with": str(current_user.id)
        })
        if not share:
            raise HTTPException(
                status_code=403,
                detail=api_response(
                    request=request,
                    success=False,
                    message_key="deck.not_authorized"
                )
            )
    
    # Get files
    files = await FileModel.find({"deck_id": deck_id}).skip(offset).limit(limit).sort("-created_at").to_list()
    total = await FileModel.find({"deck_id": deck_id}).count()
    
    # Regenerate presigned URLs
    files_data = []
    for file in files:
        url = get_presigned_url(file.minio_id, expiry_days=7)
        thumbnail_url = None
        if file.thumbnail_url:
            thumbnail_url = get_presigned_url(file.thumbnail_url, expiry_days=7)
        
        files_data.append(DeckFileItem(
            id=str(file.id),
            original_name=file.original_name,
            url=url if not thumbnail else (thumbnail_url or url),
            thumbnail_url=thumbnail_url,
            size=file.size,
            file_type=file.file_type,
            created_at=file.created_at
        ))
    
    pages = (total + limit - 1) // limit
    page = offset // limit + 1
    
    return api_response(
        request=request,
        success=True,
        data=DeckFilesData(
            files=files_data,
            total=total,
            page=page,
            pages=pages
        ).model_dump()
    )
