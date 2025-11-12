# backend/app/utils/export.py
from app.models.deck import Deck
from app.models.step import Step
from app.models.file import FileModel
from app.utils.minio_client import get_minio_client
import base64
from typing import Optional
import re
import httpx

async def export_deck_to_html(deck_id: str) -> str:
    """Export deck to standalone HTML file with embedded impress.js"""
    
    deck = await Deck.get(deck_id)
    if not deck:
        raise ValueError("Deck not found")
    
    # Get steps
    steps = await Step.find({"deck_id": deck_id}).to_list()
    
    # Sort by deck order
    step_dict = {str(step.id): step for step in steps}
    ordered_steps = [step_dict[step_id] for step_id in deck.order if step_id in step_dict]
    
    # Collect font URLs
    font_urls = set()
    for step in ordered_steps:
        if step.font_family:
            font_urls.add(step.font_family)
    
    # Generate font link tags
    font_links = "\n".join([
        f'    <link href="{url}" rel="stylesheet">'
        for url in font_urls if url.startswith('http')
    ])
    
    # Process images in step HTML
    async def process_images(html: str) -> str:
        """Convert images to base64 if < 100KB, otherwise keep as relative path"""
        # Find all img tags
        img_pattern = r'<img([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>'
        
        async def replace_img(match):
            attrs_before = match.group(1)
            src = match.group(2)
            attrs_after = match.group(3)
            
            # Check if it's a presigned URL from MinIO
            if 'minio' in src.lower() or 'decks' in src:
                try:
                    # Try to get file from MinIO
                    async with httpx.AsyncClient() as client:
                        response = await client.get(src, timeout=5.0)
                        if response.status_code == 200:
                            img_data = response.content
                            img_size_kb = len(img_data) / 1024
                            
                            if img_size_kb < 100:
                                # Convert to base64
                                img_base64 = base64.b64encode(img_data).decode('utf-8')
                                # Detect MIME type
                                content_type = response.headers.get('content-type', 'image/jpeg')
                                return f'<img{attrs_before}src="data:{content_type};base64,{img_base64}"{attrs_after}>'
                            else:
                                # Keep as relative path (note for /assets folder)
                                return f'<img{attrs_before}src="{src}"{attrs_after}><!-- Large image, copy to /assets folder -->'
                except:
                    pass
            
            # If not from MinIO or error, keep original
            return match.group(0)
        
        # Replace all images
        result = html
        matches = list(re.finditer(img_pattern, html))
        for match in matches:
            replacement = await replace_img(match)
            result = result.replace(match.group(0), replacement, 1)
        
        return result
    
    # Generate step HTML with processed images
    steps_html = ""
    for step in ordered_steps:
        font_style = f"font-family: {step.font_family};" if step.font_family else ""
        processed_html = await process_images(step.inner_html)
        
        steps_html += f'''
    <div class="step{'slide' if step.is_slide else ''}" 
         data-x="{step.data_x}" 
         data-y="{step.data_y}" 
         data-z="{step.data_z}"
         data-rotate="{step.data_rotate}"
         data-rotate-x="{step.data_rotate_x}"
         data-rotate-y="{step.data_rotate_y}"
         data-rotate-z="{step.data_rotate_z}"
         data-scale="{step.data_scale}"
         data-transition-duration="{step.data_transition_duration}"
         {'data-autoplay="' + str(step.data_autoplay) + '"' if step.data_autoplay else ''}
         style="{font_style}">
        {processed_html}
    </div>
'''
    
    # Overview step
    overview_html = ""
    if deck.has_overview:
        overview_html = f'''
    <div id="overview" class="step" 
         data-x="{deck.overview_x}" 
         data-y="{deck.overview_y}" 
         data-z="{deck.overview_z}"
         data-scale="{deck.overview_scale}">
    </div>
'''
    
    # Download impress.js and inline it
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://cdn.jsdelivr.net/npm/impress.js@2.0.0/js/impress.min.js", timeout=10.0)
            impress_js = response.text if response.status_code == 200 else ""
    except:
        impress_js = ""
    
    # Generate complete HTML
    html = f'''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{deck.title}</title>
    
{font_links}
    
    <style>
        body {{
            font-family: sans-serif;
            min-height: 740px;
            background: {deck.background_color};
        }}
        
        .step {{
            position: relative;
            width: {deck.data_width}px;
            height: {deck.data_height}px;
            padding: 40px;
            box-sizing: border-box;
        }}
        
        .impress-enabled .step {{
            margin: 0;
            opacity: 0.3;
            transition: opacity 1s;
        }}
        
        .impress-enabled .step.active {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <div id="impress" 
         data-width="{deck.data_width}"
         data-height="{deck.data_height}"
         data-max-scale="{deck.data_max_scale or ''}"
         data-min-scale="{deck.data_min_scale or ''}"
         data-perspective="{deck.data_perspective}"
         {'data-autoplay="' + str(deck.data_autoplay) + '"' if deck.data_autoplay else ''}>
{steps_html}
{overview_html}
    </div>
    
    <script>
{impress_js}
        impress().init();
    </script>
</body>
</html>'''
    
    return html

