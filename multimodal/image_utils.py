"""
Image utilities for multimodal content analysis
Handles image encoding, screenshots, and basic processing
"""

import base64
import io
from pathlib import Path
from typing import Optional, Tuple, Union
from PIL import Image
from logger import get_logger

logger = get_logger(__name__)


def encode_image_to_base64(
    image_source: Union[str, Path, Image.Image, bytes],
    format: str = 'PNG',
    max_size: Optional[Tuple[int, int]] = None
) -> str:
    """
    Encode an image to base64 string for API transmission

    Args:
        image_source: Path to image file, PIL Image, or raw bytes
        format: Image format for encoding (PNG, JPEG, WEBP)
        max_size: Optional (width, height) to resize image before encoding

    Returns:
        Base64-encoded image string
    """
    try:
        # Load image based on source type
        if isinstance(image_source, (str, Path)):
            image = Image.open(image_source)
            logger.debug(f"Loaded image from file: {image_source}")
        elif isinstance(image_source, bytes):
            image = Image.open(io.BytesIO(image_source))
            logger.debug("Loaded image from bytes")
        elif isinstance(image_source, Image.Image):
            image = image_source
            logger.debug("Using provided PIL Image")
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")

        # Resize if requested
        if max_size:
            image = resize_image(image, max_size, keep_aspect=True)
            logger.debug(f"Resized image to {image.size}")

        # Convert RGBA to RGB if saving as JPEG
        if format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Encode to base64
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        image_bytes = buffer.read()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')

        logger.info(f"Encoded image to base64 ({len(base64_string)} chars, {format})")
        return base64_string

    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}", exc_info=True)
        raise


def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Decode a base64 string to PIL Image

    Args:
        base64_string: Base64-encoded image data

    Returns:
        PIL Image object
    """
    try:
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes))
        logger.debug(f"Decoded base64 to image: {image.size}, {image.mode}")
        return image
    except Exception as e:
        logger.error(f"Error decoding base64 to image: {e}")
        raise


def capture_screenshot(
    url: str,
    output_path: Optional[Union[str, Path]] = None,
    width: int = 1280,
    height: int = 1024,
    full_page: bool = False
) -> Optional[Union[str, bytes]]:
    """
    Capture a screenshot of a website (requires playwright)

    Args:
        url: Website URL to capture
        output_path: Optional path to save screenshot
        width: Viewport width
        height: Viewport height
        full_page: Whether to capture full page or just viewport

    Returns:
        Path to saved screenshot or bytes if no output_path specified

    Note:
        Requires playwright: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright

        logger.info(f"Capturing screenshot of {url}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Navigate to URL
            page.goto(url, wait_until='networkidle', timeout=30000)

            # Capture screenshot
            if output_path:
                page.screenshot(path=str(output_path), full_page=full_page)
                logger.info(f"Screenshot saved to {output_path}")
                result = str(output_path)
            else:
                screenshot_bytes = page.screenshot(full_page=full_page)
                logger.info(f"Screenshot captured ({len(screenshot_bytes)} bytes)")
                result = screenshot_bytes

            browser.close()
            return result

    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        raise ImportError("Playwright required for screenshots. Install with: pip install playwright")
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}", exc_info=True)
        raise


def resize_image(
    image: Image.Image,
    target_size: Tuple[int, int],
    keep_aspect: bool = True,
    quality: int = 85
) -> Image.Image:
    """
    Resize an image to target dimensions

    Args:
        image: PIL Image to resize
        target_size: (width, height) tuple
        keep_aspect: Whether to maintain aspect ratio
        quality: JPEG quality (0-100) if relevant

    Returns:
        Resized PIL Image
    """
    if keep_aspect:
        # Calculate dimensions maintaining aspect ratio
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        logger.debug(f"Resized image to {image.size} (aspect maintained)")
    else:
        # Force exact dimensions
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        logger.debug(f"Resized image to {target_size} (exact)")

    return image


def is_image_file(file_path: Union[str, Path]) -> bool:
    """
    Check if a file is a supported image format

    Args:
        file_path: Path to file

    Returns:
        True if file is a supported image format
    """
    supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    return Path(file_path).suffix.lower() in supported_extensions


def get_image_metadata(image: Union[str, Path, Image.Image]) -> dict:
    """
    Extract metadata from an image

    Args:
        image: Path to image file or PIL Image

    Returns:
        Dictionary with metadata (size, format, mode, etc.)
    """
    try:
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = image

        metadata = {
            'size': img.size,
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
        }

        # Try to extract EXIF data if available
        if hasattr(img, '_getexif') and img._getexif():
            metadata['exif'] = img._getexif()

        logger.debug(f"Extracted image metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Error extracting image metadata: {e}")
        return {}
