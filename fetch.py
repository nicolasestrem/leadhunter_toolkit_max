import asyncio
from typing import Iterable, Mapping, Optional
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from cache_manager import read_cache, write_cache
from fetch_dynamic import fetch_dynamic
from retry_utils import async_retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)

@async_retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def fetch_one(client: httpx.AsyncClient, url: str, timeout: int = 15) -> str:
    """
    Fetch a single URL with retry logic

    Args:
        client: httpx AsyncClient instance
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content as string, or empty string on failure
    """
    try:
        logger.debug(f"Fetching: {url}")
        r = await client.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "LeadHunter/1.0"})
        r.raise_for_status()
        logger.info(f"Successfully fetched: {url} ({len(r.text)} chars)")
        return r.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error for {url}: {e}")
        return ""
    except httpx.TimeoutException as e:
        logger.warning(f"Timeout fetching {url}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""

async def fetch_many(
    urls: list[str],
    *,
    timeout: int = 15,
    concurrency: int = 6,
    use_cache: bool = True,
    dynamic_rendering: bool = False,
    dynamic_allowlist: Optional[Iterable[str]] = None,
    dynamic_selector_hints: Optional[Mapping[str, Iterable[str]]] = None,
) -> dict[str, str]:
    """Fetch multiple URLs concurrently with optional dynamic rendering."""
    out = {}
    sem = asyncio.Semaphore(concurrency)

    if dynamic_allowlist is not None:
        allowed_domains = {domain.lower() for domain in dynamic_allowlist}
    else:
        allowed_domains = None

    selector_hints = {
        domain.lower(): tuple(hints)
        for domain, hints in (dynamic_selector_hints or {}).items()
    }

    def _should_use_dynamic(url: str) -> bool:
        if not dynamic_rendering:
            return False
        domain = urlparse(url).netloc.lower()
        if allowed_domains is not None:
            return domain in allowed_domains
        return True

    def _cache_key(url: str, is_dynamic: bool) -> str:
        return f"dynamic::{url}" if is_dynamic else url

    logger.info(f"Fetching {len(urls)} URLs (concurrency: {concurrency}, cache: {use_cache})")

    async with httpx.AsyncClient() as client:
        async def task(url):
            # Try cache first
            dynamic = _should_use_dynamic(url)
            cache_key = _cache_key(url, dynamic)
            if use_cache:
                cached = read_cache(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {url}")
                    out[url] = cached
                    return

            # Fetch with concurrency control
            async with sem:
                if dynamic:
                    hints = selector_hints.get(urlparse(url).netloc.lower())
                    html, _ = await fetch_dynamic(
                        url,
                        timeout=timeout,
                        selector_hints=hints,
                    )
                else:
                    html = await fetch_one(client, url, timeout)
                out[url] = html

                # Write to cache if successful
                if html and use_cache:
                    if write_cache(cache_key, html):
                        logger.debug(f"Cached: {url}")

        await asyncio.gather(*(task(u) for u in urls))

    logger.info(f"Fetch complete: {len([h for h in out.values() if h])} successful out of {len(urls)}")
    return out

def extract_links(html: str, base_url: str) -> list[str]:
    """
    Extract all links from HTML

    Args:
        html: HTML content
        base_url: Base URL for link context (not currently used for joining)

    Returns:
        List of href values
    """
    try:
        tree = HTMLParser(html)
        hrefs = []
        for a in tree.css("a[href]"):
            href = a.attributes.get("href")
            if href:
                hrefs.append(href)
        logger.debug(f"Extracted {len(hrefs)} links")
        return hrefs
    except Exception as e:
        logger.error(f"Error extracting links: {e}")
        return []

def text_content(html: str) -> str:
    """
    Extract plain text content from HTML

    Args:
        html: HTML content

    Returns:
        Plain text with whitespace normalized
    """
    try:
        tree = HTMLParser(html)
        text = tree.text(separator=" ", strip=True)
        logger.debug(f"Extracted {len(text)} chars of text")
        return text
    except Exception as e:
        logger.error(f"Error extracting text content: {e}")
        return ""
