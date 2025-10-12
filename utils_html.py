import re
import tldextract
from urllib.parse import urljoin, urlparse

# Pre-compiled regex patterns for performance
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}")
WHITESPACE_RE = re.compile(r"\s+")

SOCIAL_KEYS = {
    "facebook": ["facebook.com"],
    "instagram": ["instagram.com"],
    "linkedin": ["linkedin.com", "lnkd.in"],
    "twitter": ["twitter.com", "x.com"],
    "youtube": ["youtube.com", "youtu.be"]
}

def normalize_url(base, link):
    try:
        return urljoin(base, link)
    except (ValueError, TypeError):
        # Invalid URL format or None values
        return link

def domain_of(url: str) -> str:
    try:
        ext = tldextract.extract(url)
        return ".".join(part for part in [ext.domain, ext.suffix] if part)
    except (ValueError, TypeError, AttributeError):
        # Invalid URL, None value, or extraction failure
        return ""

def find_emails(text: str) -> list[str]:
    return sorted(set(EMAIL_RE.findall(text)))

def find_phones(text: str) -> list[str]:
    """
    Extract phone numbers from text

    Args:
        text: Text to search

    Returns:
        Sorted list of unique phone numbers
    """
    phones = set()
    for m in PHONE_RE.finditer(text):
        # Use pre-compiled regex for whitespace normalization
        s = WHITESPACE_RE.sub(" ", m.group(0)).strip()
        # Count only digits, require at least 8
        if len(re.sub(r"\D", "", s)) >= 8:
            phones.add(s)
    return sorted(phones)

def collect_social(links: list[str]) -> dict[str, str]:
    out = {}
    for label, needles in SOCIAL_KEYS.items():
        for url in links:
            low = url.lower()
            if any(n in low for n in needles):
                out[label] = url
    return out

def looks_contact_or_about(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in ["contact", "about", "à propos", "qui sommes", "nous contacter"])
