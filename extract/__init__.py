"""Core contact extraction helpers.

This module provides the main interface for extracting contact information
from HTML documents. It combines both basic HTML parsing and structured data
parsing to extract emails, phone numbers, social media links, and other
contact details.

Main Functions:
    extract_basic: Extract contact signals from an HTML document
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Set
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from logger import get_logger
from name_clean import company_name_from_title
from utils_html import collect_social, domain_of, find_emails, find_phones

from .structured import parse_structured_contacts

logger = get_logger(__name__)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    """Return a sorted list of unique non-empty values.
    
    Args:
        values: An iterable of string values
        
    Returns:
        A sorted list of unique non-empty strings
    """
    return sorted({v for v in values if v})


def _resolve_structured_toggle(settings: Dict) -> bool:
    """Determine if structured data extraction should be enabled.
    
    Checks for various setting keys that might control structured data extraction.
    
    Args:
        settings: Dictionary of extraction settings
        
    Returns:
        True if structured data extraction should be enabled, False otherwise
    """
    for key in ("extract_structured", "structured", "structured_data"):
        if key in settings:
            return bool(settings[key])
    return True


def extract_basic(url: str, html: str, settings: Dict) -> Dict:
    """Extract contact signals from an HTML document.
    
    This function parses HTML content to extract various contact information
    including company names, emails, phone numbers, social media links,
    and address information. It supports both basic HTML parsing and
    structured data (JSON-LD and microdata) extraction.
    
    Args:
        url: The URL of the page being processed
        html: The HTML content to parse
        settings: Dictionary containing extraction settings including:
            - extract_emails: Whether to extract email addresses
            - extract_phones: Whether to extract phone numbers
            - extract_social: Whether to extract social media links
            - extract_structured: Whether to parse structured data
            - city: Optional city name to match in content
            
    Returns:
        Dictionary containing extracted contact information with keys:
        - name: Company or organization name
        - domain: Domain extracted from URL
        - website: The input URL
        - source_url: The input URL
        - emails: List of email addresses found
        - phones: List of phone numbers found
        - social: Dictionary of social media platform -> URL
        - address: Physical address if found
        - city: City name if detected
        - country: Country if detected
        - tags: List of classification tags (empty by default)
        - status: Lead status ("new" by default)
        - notes: Additional notes (None by default)
    """

    logger.debug("Extracting data from: %s", url)

    out = {
        "name": None,
        "domain": domain_of(url),
        "website": url,
        "source_url": url,
        "emails": [],
        "phones": [],
        "social": {},
        "address": None,
        "city": None,
        "country": None,
        "tags": [],
        "status": "new",
        "notes": None,
    }

    if not html:
        logger.warning("No HTML content for %s", url)
        return out

    try:
        tree = HTMLParser(html)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error parsing HTML for %s: %s", url, exc)
        return out

    title_node = tree.css_first("title")
    title = title_node.text(strip=True) if title_node else None
    out["name"] = company_name_from_title(title) or title

    if not out["name"]:
        h1 = tree.css_first("h1")
        if h1:
            out["name"] = h1.text(strip=True)

    logger.debug("Initial extracted name: %s", out["name"])

    links = []
    for anchor in tree.css("a[href]"):
        href = anchor.attributes.get("href")
        if href:
            links.append(urljoin(url, href))

    social_links = {}
    if settings.get("extract_social", True):
        social_links = collect_social(links)
        if social_links:
            logger.debug("Found social links: %s", list(social_links.keys()))

    text_content = tree.text(separator=" ", strip=True)

    email_values: Set[str] = set()
    if settings.get("extract_emails", True):
        mailtos = [a.attributes.get("href") for a in tree.css('a[href^="mailto:"]')]
        mt_emails = [m.split("mailto:")[-1].split("?")[0] for m in mailtos if m]
        email_values.update(find_emails(text_content))
        email_values.update(mt_emails)
        if email_values:
            logger.info("Found %d emails in page text", len(email_values))

    phone_values: Set[str] = set()
    if settings.get("extract_phones", True):
        phone_values.update(find_phones(text_content))
        if phone_values:
            logger.info("Found %d phones in page text", len(phone_values))

    addr_meta: Optional[str] = None
    for meta in tree.css("meta"):
        name_attr = (meta.attributes.get("name") or meta.attributes.get("property") or "").lower()
        if "og:street-address" in name_attr or "address" in name_attr:
            addr_meta = meta.attributes.get("content")
    if addr_meta:
        out["address"] = addr_meta

    if settings.get("city"):
        configured_city = str(settings["city"]).strip()
        if configured_city and configured_city.lower() in (text_content or "").lower():
            out["city"] = configured_city
            logger.debug("Matched configured city: %s", configured_city)

    if _resolve_structured_toggle(settings):
        structured = parse_structured_contacts(tree, base_url=url)
        if structured.names and not out["name"]:
            out["name"] = next(iter(structured.names))
        email_values.update(structured.emails)
        phone_values.update(structured.phones)
        for network, link in structured.social.items():
            if network not in social_links and link:
                social_links[network] = link
        if not out["address"] and structured.addresses:
            out["address"] = structured.addresses[0]
        if not out["city"] and structured.cities:
            out["city"] = next(iter(structured.cities))
        if not out["country"] and structured.countries:
            out["country"] = next(iter(structured.countries))

    out["emails"] = _sorted_unique(email_values)
    out["phones"] = _sorted_unique(phone_values)
    out["social"] = social_links

    logger.info(
        "Extraction complete for %s: %d emails, %d phones, %d social networks",
        url,
        len(out["emails"]),
        len(out["phones"]),
        len(out["social"]),
    )
    return out


__all__ = ["extract_basic"]