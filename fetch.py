import httpx, asyncio
from selectolax.parser import HTMLParser
from cache_manager import read_cache, write_cache, is_cache_valid
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

async def fetch_many(urls: list[str], timeout: int = 15, concurrency: int = 6, use_cache: bool = True) -> dict[str, str]:
    """
    Fetch multiple URLs concurrently with caching

    Args:
        urls: List of URLs to fetch
        timeout: Request timeout in seconds
        concurrency: Maximum concurrent requests
        use_cache: Whether to use cache

    Returns:
        Dictionary mapping URLs to HTML content
    """
    out = {}
    sem = asyncio.Semaphore(concurrency)

    logger.info(f"Fetching {len(urls)} URLs (concurrency: {concurrency}, cache: {use_cache})")

    async with httpx.AsyncClient() as client:
        async def task(url):
            # Try cache first
            if use_cache:
                cached = read_cache(url)
                if cached:
                    logger.debug(f"Cache hit: {url}")
                    out[url] = cached
                    return

            # Fetch with concurrency control
            async with sem:
                html = await fetch_one(client, url, timeout)
                out[url] = html

                # Write to cache if successful
                if html and use_cache:
                    if write_cache(url, html):
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
