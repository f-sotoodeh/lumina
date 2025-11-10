from fastapi import APIRouter, Depends, HTTPException, status
from app.models.deck import Deck
from app.models.user import User
from app.dependencies import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime
from pytz import UTC

router = APIRouter()

# Pydantic schemas
class DeckCreate(BaseModel):
    title: str
    background_color: str = "#ffffff"

class DeckOut(BaseModel):
    id: str
    title: str
    is_public: bool
    preview_url: str
    background_color: str
    thumbnail_url: str | None
    created_at: str
    updated_at: str

@router.post("/", response_model=DeckOut)
async def create_deck(payload: DeckCreate, current_user: User = Depends(get_current_user)):
    deck = Deck(
        title=payload.title,
        background_color=payload.background_color,
        owner_id=str(current_user.id),
        preview_url=str(deck.preview_url)  # UUID already generated
    )
    await deck.insert()
    return deck

@router.get("/", response_model=List[DeckOut])
async def get_my_decks(current_user: User = Depends(get_current_user)):
    decks = await Deck.find({"owner_id": str(current_user.id)}).to_list()
    return decks

@router.get("/{deck_id}", response_model=DeckOut)
async def get_deck(deck_id: str, current_user: User = Depends(get_current_user)):
    deck = await Deck.get(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.owner_id != str(current_user.id):
        raise HTTPException(403, "Not authorized")
    return deck

@router.put("/{deck_id}")
async def update_deck(deck_id: str, payload: DeckCreate, current_user: User = Depends(get_current_user)):
    deck = await Deck.get(deck_id)
    if not deck or deck.owner_id != str(current_user.id):
        raise HTTPException(404 if not deck else 403)
    deck.title = payload.title
    deck.background_color = payload.background_color
    deck.updated_at = datetime.now(UTC)
    await deck.save()
    return {"msg": "Updated"}

@router.delete("/{deck_id}")
async def delete_deck(deck_id: str, current_user: User = Depends(get_current_user)):
    deck = await Deck.get(deck_id)
    if not deck or deck.owner_id != str(current_user.id):
        raise HTTPException(404 if not deck else 403)
    await deck.delete()
    return {"msg": "Deleted"}