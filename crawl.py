import asyncio, re
from urllib.parse import urljoin, urlparse
from fetch import fetch_many, extract_links, text_content
from utils_html import looks_contact_or_about
from robots_util import robots_allowed

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
    # BFS up to max_pages within same host; prioritize likely contact/about links
    seen = set([root_url])
    to_visit = [root_url]
    pages = {}
    base_netloc = urlparse(root_url).netloc

    async def fetch_round(urls):
        # filter robots
        urls = [u for u in urls if robots_allowed(u)]
        htmls = await fetch_many(urls, timeout=timeout, concurrency=concurrency, use_cache=True)
        pages.update({u: h for u, h in htmls.items() if h})

    # first fetch home
    await fetch_round([root_url])
    if not deep_contact or len(pages) >= max_pages:
        return pages

    # collect candidate links from home
    home_html = pages.get(root_url, "")
    cands = []
    if home_html:
        links = extract_links(home_html, root_url)
        # normalize join
        links = [urljoin(root_url, l) for l in links]
        for l in links:
            if l not in seen and should_visit(base_netloc, l):
                seen.add(l)
                if any(w in l.lower() for w in CONTACT_WORDS):
                    cands.insert(0, l)  # prioritize
                else:
                    cands.append(l)

    # visit in small batches until max_pages
    visit_list = []
    for l in cands:
        if len(visit_list) + len(pages) >= max_pages:
            break
        visit_list.append(l)
    if visit_list:
        await fetch_round(visit_list)
    return pages
