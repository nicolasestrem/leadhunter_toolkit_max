import asyncio, re
from urllib.parse import urljoin, urlparse
from fetch import fetch_many, extract_links, text_content
from utils_html import looks_contact_or_about
from robots_util import robots_allowed
from logger import get_logger

logger = get_logger(__name__)

CONTACT_WORDS = ["contact", "contactez", "à propos", "apropos", "about", "impressum", "mentions", "legal", "legal notice"]

def should_visit(base_netloc: str, href: str) -> bool:
    try:
        p = urlparse(href)
        if p.scheme not in ("http", "https"):
            return False
        return p.netloc == base_netloc
    except Exception:
        return False

async def crawl_site(root_url: str, timeout: int = 15, concurrency: int = 6, max_pages: int = 5, deep_contact: bool = True):
    """
    Crawl a website starting from root URL using BFS algorithm

    Args:
        root_url: Starting URL
        timeout: Fetch timeout in seconds
        concurrency: Maximum concurrent requests
        max_pages: Maximum pages to crawl
        deep_contact: Whether to prioritize contact/about pages

    Returns:
        Dictionary mapping URLs to HTML content
    """
    logger.info(f"Starting crawl: {root_url} (max_pages: {max_pages}, deep_contact: {deep_contact})")

    seen = set([root_url])
    to_visit = [root_url]
    pages = {}
    base_netloc = urlparse(root_url).netloc

    async def fetch_round(urls):
        # Filter robots
        allowed_urls = [u for u in urls if robots_allowed(u)]
        blocked = len(urls) - len(allowed_urls)
        if blocked > 0:
            logger.debug(f"Blocked {blocked} URLs by robots.txt")

        htmls = await fetch_many(allowed_urls, timeout=timeout, concurrency=concurrency, use_cache=True)
        pages.update({u: h for u, h in htmls.items() if h})

    # First fetch home
    await fetch_round([root_url])
    logger.info(f"Fetched home page, got {len(pages)} pages")

    if not deep_contact or len(pages) >= max_pages:
        logger.info(f"Crawl complete: {len(pages)} pages")
        return pages

    # Collect candidate links from home
    home_html = pages.get(root_url, "")
    cands = []

    if home_html:
        links = extract_links(home_html, root_url)
        # Normalize join
        links = [urljoin(root_url, l) for l in links]
        logger.debug(f"Found {len(links)} links on home page")

        contact_priority = 0
        for l in links:
            if l not in seen and should_visit(base_netloc, l):
                seen.add(l)
                if any(w in l.lower() for w in CONTACT_WORDS):
                    cands.insert(0, l)  # prioritize
                    contact_priority += 1
                else:
                    cands.append(l)

        logger.info(f"Found {len(cands)} candidate URLs ({contact_priority} contact/about pages prioritized)")

    # Visit in small batches until max_pages
    visit_list = []
    for l in cands:
        if len(visit_list) + len(pages) >= max_pages:
            break
        visit_list.append(l)

    if visit_list:
        logger.info(f"Crawling {len(visit_list)} additional pages")
        await fetch_round(visit_list)

    logger.info(f"Crawl complete: {len(pages)} total pages")
    return pages
