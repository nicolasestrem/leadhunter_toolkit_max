"""
PDF utilities for text extraction and OCR
Handles PDF parsing and image-based text extraction
"""

from pathlib import Path
from typing import List, Optional, Union
from PIL import Image
from logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(
    pdf_path: Union[str, Path],
    pages: Optional[List[int]] = None
) -> str:
    """
    Extract text from PDF file

    Args:
        pdf_path: Path to PDF file
        pages: Optional list of specific pages to extract (0-indexed)

    Returns:
        Extracted text as string

    Note:
        Requires py pdf2: pip install pypdf2
    """
    try:
        import pypdf

        logger.info(f"Extracting text from PDF: {pdf_path}")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        extracted_text = []

        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            total_pages = len(reader.pages)

            logger.debug(f"PDF has {total_pages} pages")

            # Determine which pages to process
            if pages is None:
                pages_to_process = range(total_pages)
            else:
                pages_to_process = [p for p in pages if 0 <= p < total_pages]

            # Extract text from each page
            for page_num in pages_to_process:
                page = reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}\n")
                    logger.debug(f"Extracted {len(text)} chars from page {page_num + 1}")

        full_text = '\n'.join(extracted_text)
        logger.info(f"Extracted {len(full_text)} total characters from PDF")
        return full_text

    except ImportError:
        logger.error("pypdf not installed. Run: pip install pypdf")
        raise ImportError("pypdf required for PDF text extraction. Install with: pip install pypdf")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        raise


def pdf_to_images(
    pdf_path: Union[str, Path],
    pages: Optional[List[int]] = None,
    dpi: int = 200
) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images

    Args:
        pdf_path: Path to PDF file
        pages: Optional list of specific pages to convert (0-indexed)
        dpi: Resolution for rendering (default 200)

    Returns:
        List of PIL Image objects

    Note:
        Requires pdf2image: pip install pdf2image
        Also requires poppler: https://github.com/oschwartz10612/poppler-windows/releases
    """
    try:
        from pdf2image import convert_from_path

        logger.info(f"Converting PDF to images: {pdf_path} at {dpi} DPI")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Convert PDF to images
        if pages:
            # Convert specific pages (pdf2image uses 1-indexed pages)
            images = []
            for page_num in pages:
                page_images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    first_page=page_num + 1,
                    last_page=page_num + 1
                )
                images.extend(page_images)
        else:
            # Convert all pages
            images = convert_from_path(pdf_path, dpi=dpi)

        logger.info(f"Converted {len(images)} pages to images")
        return images

    except ImportError:
        logger.error("pdf2image not installed. Run: pip install pdf2image")
        raise ImportError("pdf2image required. Install with: pip install pdf2image")
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}", exc_info=True)
        raise


def ocr_pdf_page(
    pdf_path: Union[str, Path],
    page_num: int = 0,
    dpi: int = 200,
    lang: str = 'eng'
) -> str:
    """
    Perform OCR on a PDF page

    Args:
        pdf_path: Path to PDF file
        page_num: Page number to OCR (0-indexed)
        dpi: Resolution for rendering
        lang: Tesseract language code (eng, deu, fra, etc.)

    Returns:
        Extracted text from OCR

    Note:
        Requires pytesseract: pip install pytesseract
        Also requires Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    """
    try:
        import pytesseract

        logger.info(f"Performing OCR on PDF page {page_num + 1} with language: {lang}")

        # Convert PDF page to image
        images = pdf_to_images(pdf_path, pages=[page_num], dpi=dpi)

        if not images:
            logger.warning(f"No images generated from page {page_num}")
            return ""

        # Perform OCR on the image
        text = pytesseract.image_to_string(images[0], lang=lang)

        logger.info(f"OCR extracted {len(text)} characters")
        return text

    except ImportError:
        logger.error("pytesseract not installed. Run: pip install pytesseract")
        raise ImportError("pytesseract required for OCR. Install with: pip install pytesseract")
    except Exception as e:
        logger.error(f"Error performing OCR: {e}", exc_info=True)
        raise


def extract_text_hybrid(
    pdf_path: Union[str, Path],
    pages: Optional[List[int]] = None,
    use_ocr_fallback: bool = True,
    ocr_lang: str = 'eng'
) -> str:
    """
    Extract text from PDF with OCR fallback for scanned pages

    Args:
        pdf_path: Path to PDF file
        pages: Optional list of specific pages
        use_ocr_fallback: Whether to use OCR if text extraction fails
        ocr_lang: Language for OCR

    Returns:
        Extracted text
    """
    try:
        # First, try standard text extraction
        text = extract_text_from_pdf(pdf_path, pages)

        # Check if we got meaningful text
        if len(text.strip()) < 50 and use_ocr_fallback:
            logger.info("Limited text found, falling back to OCR")

            # Try OCR on the pages
            ocr_texts = []
            pages_to_ocr = pages if pages else [0]  # OCR first page by default

            for page_num in pages_to_ocr:
                try:
                    ocr_text = ocr_pdf_page(pdf_path, page_num, lang=ocr_lang)
                    if ocr_text.strip():
                        ocr_texts.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}\n")
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue

            if ocr_texts:
                text = '\n'.join(ocr_texts)
                logger.info(f"OCR extracted {len(text)} characters")

        return text

    except Exception as e:
        logger.error(f"Error in hybrid text extraction: {e}")
        raise


def get_pdf_metadata(pdf_path: Union[str, Path]) -> dict:
    """
    Extract metadata from PDF file

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with PDF metadata
    """
    try:
        import pypdf

        pdf_path = Path(pdf_path)
        metadata = {}

        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)

            metadata['pages'] = len(reader.pages)
            metadata['encrypted'] = reader.is_encrypted

            # Extract document info if available
            if reader.metadata:
                metadata['title'] = reader.metadata.get('/Title', '')
                metadata['author'] = reader.metadata.get('/Author', '')
                metadata['subject'] = reader.metadata.get('/Subject', '')
                metadata['creator'] = reader.metadata.get('/Creator', '')

        logger.debug(f"Extracted PDF metadata: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {e}")
        return {}
