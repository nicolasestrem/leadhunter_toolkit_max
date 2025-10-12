# Multimodal Support - Lead Hunter Toolkit

Multimodal capabilities for visual content analysis, including screenshots, images, and PDF OCR.

## Features

- **Image Analysis**: Analyze screenshots, logos, marketing materials
- **Website Screenshot Analysis**: Automated capture and analysis
- **PDF Text Extraction**: Extract text from PDFs with OCR fallback
- **Vision API Integration**: Seamless integration with LLM adapter

## Installation

### Required Packages

```bash
# Core image processing
pip install Pillow

# PDF text extraction
pip install pypdf

# Screenshot capture (optional)
pip install playwright
playwright install chromium

# PDF to image conversion (optional)
pip install pdf2image
# Also requires poppler: https://github.com/oschwartz10612/poppler-windows/releases

# OCR support (optional)
pip install pytesseract
# Also requires Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

### Vision-Capable Models

Multimodal features require a vision-capable LLM:
- OpenAI: `gpt-4-vision-preview`, `gpt-4o`, `gpt-4o-mini`
- Anthropic: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- Google: `gemini-pro-vision`

Update your LLM configuration in settings to use a vision model.

## Usage

### 1. Image Analysis

```python
from llm.adapter import LLMAdapter
from config.loader import ConfigLoader

# Initialize adapter
config_loader = ConfigLoader()
config = config_loader.get_merged_config()
llm = LLMAdapter.from_config(config)

# Analyze an image
response = llm.chat_with_image(
    prompt="Describe the branding and design quality of this logo",
    image_data="path/to/logo.png"
)

print(response)
```

### 2. Screenshot Analysis

```python
# Capture and analyze website screenshot
result = llm.analyze_screenshot(
    url="https://example.com",
    analysis_prompt="""Analyze this website and provide:
    1. Overall design quality
    2. Mobile responsiveness indicators
    3. Key call-to-actions
    4. Branding consistency""",
    capture_full_page=False
)

print(result['analysis'])
print(f"Screenshot saved to: {result['screenshot_path']}")
```

### 3. Multiple Images

```python
# Analyze multiple images together
images = [
    "path/to/homepage.png",
    "path/to/product_page.png",
    "path/to/checkout.png"
]

response = llm.chat_with_images(
    prompt="Compare these three pages and identify design inconsistencies",
    images=images
)
```

### 4. PDF Text Extraction

```python
from multimodal import extract_text_from_pdf, extract_text_hybrid

# Standard text extraction
text = extract_text_from_pdf("document.pdf", pages=[0, 1, 2])
print(text)

# Hybrid extraction with OCR fallback
text = extract_text_hybrid(
    "scanned_document.pdf",
    pages=[0],
    use_ocr_fallback=True,
    ocr_lang='eng'
)
```

### 5. Image Utilities

```python
from multimodal import (
    encode_image_to_base64,
    resize_image,
    capture_screenshot,
    is_image_file
)

# Encode image to base64
base64_str = encode_image_to_base64(
    "image.jpg",
    format='JPEG',
    max_size=(2048, 2048)  # Resize before encoding
)

# Capture screenshot
screenshot_bytes = capture_screenshot(
    "https://example.com",
    width=1280,
    height=1024,
    full_page=False
)

# Check if file is an image
if is_image_file("file.png"):
    print("This is an image file")
```

## Integration with Consulting Pack

### Dossier Enhancement

```python
from dossier.build import build_dossier
from llm.adapter import LLMAdapter

# Build dossier with visual analysis
llm = LLMAdapter.from_config(config)

# Analyze lead's website visually
screenshot_analysis = llm.analyze_screenshot(
    url=lead_data['website'],
    analysis_prompt="""Analyze this business website and provide:
    1. Brand professionalism score (1-10)
    2. Mobile-friendliness indicators
    3. Visual appeal and modern design elements
    4. Clear value proposition visibility
    5. Trust signals present"""
)

# Include in dossier
dossier = build_dossier(lead_data, llm)
dossier['visual_analysis'] = screenshot_analysis['analysis']
```

### Audit Enhancement

```python
from audit.page_audit import audit_page

# Audit with visual assessment
visual_issues = llm.chat_with_image(
    prompt="""Identify visual/UX issues:
    1. Readability problems
    2. Poor contrast
    3. Cluttered layouts
    4. Missing visual hierarchy
    5. Broken images or styling""",
    image_data=screenshot_path
)

audit_result['visual_issues'] = visual_issues
```

## Use Cases

### 1. Restaurant Lead Analysis

```python
# Analyze restaurant's social media images
instagram_images = [
    "food_photo1.jpg",
    "interior_photo.jpg",
    "menu_board.jpg"
]

analysis = llm.chat_with_images(
    prompt="""Analyze these restaurant images and assess:
    1. Food presentation quality
    2. Interior ambiance and cleanliness
    3. Menu readability and appeal
    4. Overall professionalism""",
    images=instagram_images
)
```

### 2. Retail Store Visual Assessment

```python
# Analyze storefront and product displays
storefront_analysis = llm.chat_with_image(
    prompt="""Assess this retail storefront:
    1. Window display effectiveness
    2. Signage visibility and quality
    3. Accessibility and welcoming appearance
    4. Brand consistency""",
    image_data="storefront.jpg"
)
```

### 3. PDF Brochure Analysis

```python
# Extract text from marketing PDF
brochure_text = extract_text_from_pdf("company_brochure.pdf")

# Analyze brochure images
pdf_images = pdf_to_images("company_brochure.pdf", pages=[0])
cover_analysis = llm.chat_with_image(
    prompt="Analyze the design quality and messaging of this brochure cover",
    image_data=encode_image_to_base64(pdf_images[0])
)
```

## Configuration

### Enable Vision in LLM Config

Update `config/defaults.yml`:

```yaml
llm:
  base_url: "https://api.openai.com"
  model: "gpt-4o"  # Vision-capable model
  api_key: "your-api-key"
  temperature: 0.2
  max_tokens: 2048
```

### Screenshot Settings

Configure screenshot capture behavior:

```python
# Custom screenshot settings
screenshot_config = {
    'width': 1920,
    'height': 1080,
    'full_page': True,
    'wait_until': 'networkidle'
}
```

## Error Handling

```python
try:
    result = llm.analyze_screenshot(url="https://example.com")
    if 'error' in result:
        print(f"Screenshot capture failed: {result['error']}")
    else:
        print(f"Analysis: {result['analysis']}")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install playwright")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Image Size Optimization

```python
# Resize images before encoding to reduce API costs
base64_str = encode_image_to_base64(
    "large_image.jpg",
    format='JPEG',
    max_size=(2048, 2048)  # Max dimension
)
```

### Detail Levels

```python
# Use 'low' detail for faster/cheaper processing
response = llm.chat_with_image(
    prompt="Quick overview of this image",
    image_data="image.jpg",
    detail="low"  # 'low', 'high', or 'auto'
)
```

### Batch Processing

```python
# Process multiple screenshots concurrently
import asyncio

async def analyze_multiple_sites(urls):
    tasks = [
        llm.chat_with_image_async(
            prompt="Analyze this website",
            image_data=await capture_screenshot_async(url)
        )
        for url in urls
    ]
    return await asyncio.gather(*tasks)
```

## Limitations

1. **Model Requirements**: Requires vision-capable models (gpt-4o, claude-3, etc.)
2. **API Costs**: Vision API calls are more expensive than text-only
3. **Image Size Limits**: Most APIs have ~20MB limit per image
4. **Screenshot Dependencies**: Playwright requires Chromium installation
5. **OCR Accuracy**: OCR quality depends on image/PDF quality

## Troubleshooting

### Playwright Not Installed
```bash
pip install playwright
playwright install chromium
```

### PDF2Image Missing Poppler
Download from: https://github.com/oschwartz10612/poppler-windows/releases
Add to PATH

### Tesseract Not Found
Download from: https://github.com/UB-Mannheim/tesseract/wiki
Add to PATH

### Vision API Not Supported
Ensure your model supports vision:
- Check model documentation
- Update to vision-capable model in config
- Verify API key has vision access

## Future Enhancements

- [ ] Video frame extraction and analysis
- [ ] Social media post scraping and analysis
- [ ] Competitive visual comparison
- [ ] Brand consistency scoring
- [ ] Automated A/B testing of visual elements
- [ ] Real-time screenshot monitoring

## References

- OpenAI Vision API: https://platform.openai.com/docs/guides/vision
- Anthropic Claude Vision: https://docs.anthropic.com/claude/docs/vision
- Playwright: https://playwright.dev/python/
- PyPDF: https://pypdf.readthedocs.io/
- Tesseract OCR: https://github.com/tesseract-ocr/tesseract
