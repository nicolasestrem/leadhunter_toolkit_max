# Content scrapers and normalizers for Markdown Mode-like usage.
# If you already have raw HTML, convert to markdown or plain text here.
from selectolax.parser import HTMLParser
from selectolax.parser import ParserError

def to_markdown(html: str) -> str:
    try:
        # very light markdown from headings and paragraphs
        tree = HTMLParser(html)
        parts = []
        for h in tree.css("h1, h2, h3"):
            parts.append("# " + h.text(strip=True))
        for p in tree.css("p"):
            parts.append(p.text(separator=" ", strip=True))
        return "\n\n".join([p for p in parts if p])
    except (ParserError, AttributeError, TypeError):
        # HTML parsing error, or invalid HTML structure
        return ""
