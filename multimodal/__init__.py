"""
Multimodal utilities for visual content analysis
Supports screenshots, images, and PDF OCR
"""

from multimodal.image_utils import (
    encode_image_to_base64,
    decode_base64_to_image,
    capture_screenshot,
    resize_image,
    is_image_file
)

from multimodal.pdf_utils import (
    extract_text_from_pdf,
    pdf_to_images,
    ocr_pdf_page
)

__all__ = [
    'encode_image_to_base64',
    'decode_base64_to_image',
    'capture_screenshot',
    'resize_image',
    'is_image_file',
    'extract_text_from_pdf',
    'pdf_to_images',
    'ocr_pdf_page'
]
