# Content scrapers and normalizers for Markdown Mode-like usage.
# If you already have raw HTML, convert to markdown or plain text here.
from typing import Dict, Optional, Union

from selectolax.parser import HTMLParser


def to_markdown(html: str, include_meta: bool = False) -> Union[str, Dict[str, Optional[str]]]:
    """Convert HTML to lightweight markdown and optionally return metadata."""

    def _empty():
        if include_meta:
            return {"markdown": "", "title": None, "meta_description": None}
        return ""

    try:
        # very light markdown from headings and paragraphs
        tree = HTMLParser(html)
        parts = []
        for h in tree.css("h1, h2, h3"):
            text = h.text(strip=True)
            if text:
                parts.append("# " + text)
        for p in tree.css("p"):
            text = p.text(separator=" ", strip=True)
            if text:
                parts.append(text)

        markdown = "\n\n".join(parts)
        if not include_meta:
            return markdown

        title_node = tree.css_first("title")
        title = title_node.text(strip=True) if title_node else None

        meta_desc = None
        for selector in [
            "meta[name=description]",
            "meta[name='description']",
            "meta[property='og:description']",
            "meta[name='og:description']",
        ]:
            meta_node = tree.css_first(selector)
            if meta_node and meta_node.attributes.get("content"):
                meta_desc = meta_node.attributes.get("content")
                break

        return {"markdown": markdown, "title": title, "meta_description": meta_desc}
    except Exception:
        # HTML parsing error, or invalid HTML structure
        return _empty()
