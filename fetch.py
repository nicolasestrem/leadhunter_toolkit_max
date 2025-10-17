import httpx, asyncio
from selectolax.parser import HTMLParser
from cache_manager import read_cache, write_cache, is_cache_valid
from retry_utils import async_retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)

@async_retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def fetch_one(client: httpx.AsyncClient, url: str, timeout: int = 15) -> str:
    """Fetch a single URL with retry logic.

    Args:
        client (httpx.AsyncClient): The httpx AsyncClient instance to use.
        url (str): The URL to fetch.
        timeout (int): The request timeout in seconds.

    Returns:
        str: The HTML content of the page, or an empty string on failure.
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
    """Fetch multiple URLs concurrently, with caching.

    Args:
        urls (list[str]): A list of URLs to fetch.
        timeout (int): The request timeout in seconds.
        concurrency (int): The maximum number of concurrent requests.
        use_cache (bool): If True, use the cache.

    Returns:
        dict[str, str]: A dictionary mapping URLs to their HTML content.
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
    """Extract all links from a string of HTML.

    Args:
        html (str): The HTML content.
        base_url (str): The base URL for resolving relative links.

    Returns:
        list[str]: A list of the href values of all links found.
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
    """Extract the plain text content from a string of HTML.

    Args:
        html (str): The HTML content.

    Returns:
        str: The extracted plain text, with whitespace normalized.
    """
    try:
        tree = HTMLParser(html)
        text = tree.text(separator=" ", strip=True)
        logger.debug(f"Extracted {len(text)} chars of text")
        return text
    except Exception as e:
        logger.error(f"Error extracting text content: {e}")
        return ""
