# backend/app/api/v1/endpoints/comments.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.models.comment import Comment
from app.models.step import Step
from app.models.deck import Deck
from app.models.share import Share
from app.models.user import User
from app.schemas.comment import (
    CommentCountData, CommentListData, CommentCreateData, CommentUpdateData
)
from app.schemas.common import EmptyData
from app.schemas.response import APIResponse
from app.utils.response import api_response
from app.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime
from pytz import UTC
import html

router = APIRouter()

class CreateCommentRequest(BaseModel):
    text: str

class UpdateCommentRequest(BaseModel):
    text: str

async def check_comment_access(step_id: str, user_id: str) -> tuple[Step, Deck]:
    """Check if user has access to comment on step"""
    step = await Step.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    deck = await Deck.get(step.deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Owner has access
    if deck.owner_id == user_id:
        return step, deck
    
    # Check share access (Commenter or Editor)
    share = await Share.find_one({
        "deck_id": step.deck_id,
        "share_with": user_id
    })
    
    if not share or share.access_level not in ["Commenter", "Editor"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return step, deck

@router.get("/count", response_model=APIResponse[CommentCountData])
async def get_comments_count(
    request: Request,
    deck_id: str = Query(None),
    step_id: str = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get comments count for deck or step"""
    query = {}
    if step_id:
        query["step_id"] = step_id
    elif deck_id:
        query["deck_id"] = deck_id
    
    count = await Comment.find(query).count()
    
    return api_response(
        request=request,
        success=True,
        data=CommentCountData(count=count).model_dump()
    )

@router.get("/step/{step_id}", response_model=APIResponse[CommentListData])
async def get_step_comments(
    request: Request,
    step_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a step"""
    await check_comment_access(step_id, str(current_user.id))
    
    comments = await Comment.find({"step_id": step_id}).skip(offset).limit(limit).sort("-created_at").to_list()
    total = await Comment.find({"step_id": step_id}).count()
    
    from app.schemas.comment import CommentOut
    comments_data = [CommentOut.model_validate(comment) for comment in comments]
    
    return api_response(
        request=request,
        success=True,
        data=CommentListData(comments=comments_data, total=total).model_dump()
    )

@router.post("/step/{step_id}", response_model=APIResponse[CommentCreateData])
async def create_comment(
    request: Request,
    step_id: str,
    payload: CreateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a step"""
    step, deck = await check_comment_access(step_id, str(current_user.id))
    
    # Validate text length
    if len(payload.text) > 1000:
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="comment.text_too_long"
            )
        )
    
    # Escape HTML
    escaped_text = html.escape(payload.text)
    
    comment = Comment(
        user_id=str(current_user.id),
        deck_id=step.deck_id,
        step_id=step_id,
        text=escaped_text
    )
    await comment.insert()
    
    return api_response(
        request=request,
        success=True,
        message_key="comment.created",
        data=CommentCreateData(
            id=str(comment.id),
            text=comment.text,
            created_at=comment.created_at
        ).model_dump()
    )

@router.put("/{comment_id}", response_model=APIResponse[CommentUpdateData])
async def update_comment(
    request: Request,
    comment_id: str,
    payload: UpdateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only own comments)"""
    comment = await Comment.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="comment.not_found"
            )
        )
    
    # Only owner can edit
    if comment.user_id != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail=api_response(
                request=request,
                success=False,
                message_key="comment.not_authorized"
            )
        )
    
    # Validate text length
    if len(payload.text) > 1000:
        raise HTTPException(
            status_code=400,
            detail=api_response(
                request=request,
                success=False,
                message_key="comment.text_too_long"
            )
        )
    
    # Escape HTML
    comment.text = html.escape(payload.text)
    comment.is_edited = True
    comment.updated_at = datetime.now(UTC)
    await comment.save()
    
    return api_response(
        request=request,
        success=True,
        message_key="comment.updated",
        data=CommentUpdateData(
            id=str(comment.id),
            text=comment.text,
            is_edited=comment.is_edited
        ).model_dump()
    )

@router.delete("/{comment_id}", response_model=APIResponse[EmptyData])
async def delete_comment(
    request: Request,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (own comments or Editor can delete others)"""
    comment = await Comment.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=404,
            detail=api_response(
                request=request,
                success=False,
                message_key="comment.not_found"
            )
        )
    
    # Owner can delete own comment
    if comment.user_id == str(current_user.id):
        await comment.delete()
        return api_response(
            request=request,
            success=True,
            message_key="comment.deleted",
            data=EmptyData().model_dump()
        )
    
    # Editor can delete others' comments
    deck = await Deck.get(comment.deck_id)
    if deck and deck.owner_id == str(current_user.id):
        await comment.delete()
        return api_response(
            request=request,
            success=True,
            message_key="comment.deleted",
            data=EmptyData().model_dump()
        )
    
    # Check if Editor through share
    share = await Share.find_one({
        "deck_id": comment.deck_id,
        "share_with": str(current_user.id)
    })
    
    if share and share.access_level == "Editor":
        await comment.delete()
        return api_response(
            request=request,
            success=True,
            message_key="comment.deleted",
            data=EmptyData().model_dump()
        )
    
    raise HTTPException(
        status_code=403,
        detail=api_response(
            request=request,
            success=False,
            message_key="comment.not_authorized"
        )
    )

