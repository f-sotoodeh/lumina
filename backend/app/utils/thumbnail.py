# backend/app/utils/thumbnail.py
from PIL import Image
from io import BytesIO
from typing import Literal, Tuple

ImageFormat = Literal["JPEG", "PNG", "GIF"]

def is_image_type(content_type: str) -> bool:
    """Check if content type is an image"""
    return content_type.lower().startswith('image/')

def create_thumbnail(
    image_data: bytes,
    size: Tuple[int, int] = (200, 200),
    format: ImageFormat = "JPEG"
) -> bytes:
    """
    Create thumbnail from image data
    Supports JPEG, PNG, GIF
    SVG will be rasterized first
    """
    try:
        # Try to open as regular image
        img = Image.open(BytesIO(image_data))
        
        # Convert RGBA to RGB for JPEG
        if format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        
        # Create thumbnail (maintains aspect ratio)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format=format, quality=85, optimize=True)
        return output.getvalue()
        
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        raise

def rasterize_svg(svg_data: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
    """
    Rasterize SVG to PNG
    Note: Requires cairosvg library (optional dependency)
    """
    try:
        import cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_data,
            output_width=size[0],
            output_height=size[1]
        )
        return png_data
    except ImportError:
        print("cairosvg not installed, cannot rasterize SVG")
        raise
    except Exception as e:
        print(f"Error rasterizing SVG: {e}")
        raise

def create_thumbnail_from_svg(svg_data: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
    """Create thumbnail from SVG by rasterizing first"""
    png_data = rasterize_svg(svg_data, size)
    return create_thumbnail(png_data, size, "JPEG")

