# backend/app/utils/deck_thumbnail.py
from app.models.deck import Deck
from app.models.step import Step
from app.utils.minio_client import upload_file, get_presigned_url
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio
from typing import Optional

async def generate_deck_thumbnail(deck_id: str) -> Optional[str]:
    """
    Generate 200x200 JPG thumbnail for deck
    Returns presigned URL or None if no steps
    """
    deck = await Deck.get(deck_id)
    if not deck:
        return None
    
    # Get steps
    steps = await Step.find({"deck_id": deck_id}).to_list()
    if not steps:
        return None
    
    # Sort by deck order
    step_dict = {str(step.id): step for step in steps}
    ordered_steps = [step_dict[step_id] for step_id in deck.order if step_id in step_dict]
    
    if not ordered_steps:
        return None
    
    # Get first step
    first_step = ordered_steps[0]
    
    # Create thumbnail image
    img = Image.new('RGB', (200, 200), color=deck.background_color or '#6366f1')
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()
    
    # Extract text from HTML (simple approach)
    import re
    text = re.sub('<[^<]+?>', '', first_step.inner_html)
    text = text.strip()[:50]  # Limit to 50 chars
    
    # Draw deck title and step preview
    title = deck.title[:30]
    draw.text((10, 10), title, fill='white', font=font)
    if text:
        draw.text((10, 40), text, fill='white', font=font)
    
    # Save to bytes
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    thumbnail_data = output.getvalue()
    
    # Upload to MinIO (using asyncio.to_thread for blocking I/O)
    object_name = f"decks/{deck_id}/thumbnail.jpg"
    await asyncio.to_thread(upload_file, thumbnail_data, object_name, "image/jpeg")
    
    # Get presigned URL (using asyncio.to_thread for blocking I/O)
    thumbnail_url = await asyncio.to_thread(get_presigned_url, object_name, 7)
    
    # Update deck
    deck.thumbnail_url = thumbnail_url
    await deck.save()
    
    return thumbnail_url

# Debounce mechanism for thumbnail regeneration
_thumbnail_tasks = {}

async def schedule_thumbnail_regeneration(deck_id: str, delay: float = 2.0):
    """Schedule thumbnail regeneration with debounce"""
    # Cancel existing task if any
    if deck_id in _thumbnail_tasks:
        _thumbnail_tasks[deck_id].cancel()
    
    async def regenerate():
        await asyncio.sleep(delay)
        await generate_deck_thumbnail(deck_id)
        if deck_id in _thumbnail_tasks:
            del _thumbnail_tasks[deck_id]
    
    task = asyncio.create_task(regenerate())
    _thumbnail_tasks[deck_id] = task

