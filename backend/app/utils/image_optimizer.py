# backend/app/utils/image_optimizer.py
from PIL import Image
from io import BytesIO
from typing import Optional

def optimize_image(
    image_data: bytes,
    max_size: Optional[int] = None,
    quality: int = 85
) -> bytes:
    """
    Optimize image by reducing quality and optionally resizing
    max_size: maximum dimension (width or height) in pixels
    quality: JPEG quality (1-100)
    """
    try:
        img = Image.open(BytesIO(image_data))
        
        # Resize if max_size specified
        if max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Determine output format
        output_format = img.format if img.format in ["JPEG", "PNG", "GIF"] else "JPEG"
        
        # Convert RGBA to RGB for JPEG
        if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        
        # Save optimized
        output = BytesIO()
        save_kwargs = {"optimize": True}
        if output_format == "JPEG":
            save_kwargs["quality"] = quality
        
        img.save(output, format=output_format, **save_kwargs)
        return output.getvalue()
        
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return image_data  # Return original if optimization fails

