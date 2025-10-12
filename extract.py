from typing import List, Dict
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
from utils_html import find_emails, find_phones, collect_social, looks_contact_or_about, domain_of
from name_clean import company_name_from_title

def extract_basic(url: str, html: str, settings: dict) -> dict:
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
        return out
    try:
        tree = HTMLParser(html)
    except Exception:
        return out
    title = tree.css_first("title").text(strip=True) if tree.css_first("title") else None
    out["name"] = company_name_from_title(title) or title

    # H1 as fallback
    if not out["name"]:
        h1 = tree.css_first("h1")
        if h1:
            out["name"] = h1.text(strip=True)

    # collect links for socials and contact
    links = []
    for a in tree.css("a[href]"):
        links.append(urljoin(url, a.attributes.get("href")))
    if settings.get("extract_social", True):
        out["social"] = collect_social(links)
    text = tree.text(separator=" ", strip=True)
    if settings.get("extract_emails", True):
        # include mailto
        mailtos = [a.attributes.get("href") for a in tree.css('a[href^="mailto:"]')]
        mt_emails = [m.split("mailto:")[-1].split("?")[0] for m in mailtos if m]
        out["emails"] = sorted(set(find_emails(text) + mt_emails))
    if settings.get("extract_phones", True):
        out["phones"] = find_phones(text)
    # naive address lines from meta and microdata
    addr = None
    for meta in tree.css("meta"):
        name = (meta.attributes.get("name") or meta.attributes.get("property") or "").lower()
        if "og:street-address" in name or "address" in name:
            addr = meta.attributes.get("content")
    out["address"] = addr
    # city detection simple heuristic
    city = settings.get("city", None)
    if city and city.lower() in (text or "").lower():
        out["city"] = city
    return out
