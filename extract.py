from typing import List, Dict
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from utils_html import find_emails, find_phones, collect_social, looks_contact_or_about, domain_of
from name_clean import company_name_from_title
from logger import get_logger

logger = get_logger(__name__)


def extract_basic(url: str, html: str, settings: dict) -> dict:
    """Extract basic lead information from the HTML of a web page.

    This function parses the HTML to find the company name, contact information,
    social media links, and other relevant details.

    Args:
        url (str): The source URL of the web page.
        html (str): The HTML content of the web page.
        settings (dict): A dictionary of extraction settings, such as whether
                         to extract emails, phones, and social links.

    Returns:
        dict: A dictionary containing the extracted lead data.
    """
    logger.debug(f"Extracting data from: {url}")

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
        "notes": None
    }

    if not html:
        logger.warning(f"No HTML content for {url}")
        return out

    try:
        tree = HTMLParser(html)
    except Exception as e:
        logger.error(f"Error parsing HTML for {url}: {e}")
        return out

    # Extract name from title
    title = tree.css_first("title").text(strip=True) if tree.css_first("title") else None
    out["name"] = company_name_from_title(title) or title

    # H1 as fallback
    if not out["name"]:
        h1 = tree.css_first("h1")
        if h1:
            out["name"] = h1.text(strip=True)

    logger.debug(f"Extracted name: {out['name']}")

    # Collect links for socials and contact
    links = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href")
        if href:
            links.append(urljoin(url, href))

    # Extract social links
    if settings.get("extract_social", True):
        out["social"] = collect_social(links)
        if out["social"]:
            logger.debug(f"Found social links: {list(out['social'].keys())}")

    # Extract text content
    text = tree.text(separator=" ", strip=True)

    # Extract emails
    if settings.get("extract_emails", True):
        # Include mailto links
        mailtos = [a.attributes.get("href") for a in tree.css('a[href^="mailto:"]')]
        mt_emails = [m.split("mailto:")[-1].split("?")[0] for m in mailtos if m]
        out["emails"] = sorted(set(find_emails(text) + mt_emails))
        if out["emails"]:
            logger.info(f"Found {len(out['emails'])} emails: {out['emails'][:3]}")

    # Extract phones
    if settings.get("extract_phones", True):
        out["phones"] = find_phones(text)
        if out["phones"]:
            logger.info(f"Found {len(out['phones'])} phones")

    # Extract address from meta tags
    addr = None
    for meta in tree.css("meta"):
        name = (meta.attributes.get("name") or meta.attributes.get("property") or "").lower()
        if "og:street-address" in name or "address" in name:
            addr = meta.attributes.get("content")
    out["address"] = addr

    # City detection
    city = settings.get("city", None)
    if city and city.lower() in (text or "").lower():
        out["city"] = city
        logger.debug(f"Matched city: {city}")

    logger.info(f"Extraction complete for {url}: {len(out['emails'])} emails, {len(out['phones'])} phones")
    return out
