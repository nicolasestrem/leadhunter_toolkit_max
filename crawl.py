import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import httpx

from cache_manager import read_cache, write_cache
from fetch import extract_links, fetch_one
from fetch_dynamic import fetch_dynamic
from logger import get_logger
from robots_util import USER_AGENT, get_crawl_delay, robots_allowed
from utils_html import looks_contact_or_about

logger = get_logger(__name__)


@dataclass
class CrawlConfig:
    """Configuration for the website crawler.

    This class defines parameters for controlling how the crawler behaves,
    including depth limits, domain restrictions, dynamic rendering options,
    and request handling settings.

    Attributes:
        max_depth (int): The maximum depth to crawl from the root URL.
        allowed_domains (Optional[Iterable[str]]): A list of allowed domains to crawl.
        dynamic_rendering (bool): If True, use dynamic rendering for JavaScript-heavy sites.
        dynamic_allowed_domains (Optional[Iterable[str]]): Domains that should use dynamic rendering.
        path_filters (Iterable[re.Pattern]): A list of regex patterns to filter paths.
        disallowed_extensions (Iterable[str]): A list of disallowed file extensions.
        request_delay (Optional[float]): The delay between requests in seconds.
        use_cache (bool): If True, use the cache for storing responses.
        allowed_query_params (Optional[Iterable[str]]): Query parameters to preserve.
        blocked_query_params (Iterable[str]): Query parameters to remove.
        strip_empty_fragments (bool): If True, remove empty URL fragments.
        dynamic_selector_hints (Mapping[str, Iterable[str]]): CSS selectors for dynamic content.
    """
    max_depth: int = 2
    allowed_domains: Optional[Iterable[str]] = None
    dynamic_rendering: bool = False
    dynamic_allowed_domains: Optional[Iterable[str]] = None
    path_filters: Iterable[re.Pattern] = field(default_factory=list)
    disallowed_extensions: Iterable[str] = field(default_factory=set)
    request_delay: Optional[float] = None
    use_cache: bool = True
    allowed_query_params: Optional[Iterable[str]] = None
    blocked_query_params: Iterable[str] = field(default_factory=set)
    strip_empty_fragments: bool = True
    dynamic_selector_hints: Mapping[str, Iterable[str]] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization processing to normalize and validate configuration."""
        if self.allowed_domains is not None:
            self.allowed_domains = {d.lower() for d in self.allowed_domains}
        else:
            self.allowed_domains = None

        # Support legacy attribute names that may still be attached to
        # deserialized CrawlConfig instances.
        legacy_allowlist = getattr(self, "dynamic_allowlist", None)
        if legacy_allowlist and not getattr(self, "dynamic_allowed_domains", None):
            self.dynamic_allowed_domains = legacy_allowlist
        if hasattr(self, "dynamic_allowlist"):
            delattr(self, "dynamic_allowlist")

        dynamic_domains = getattr(self, "dynamic_allowed_domains", None)
        if dynamic_domains is not None:
            self.dynamic_allowed_domains = {
                d.lower() for d in dynamic_domains if d
            }
        else:
            self.dynamic_allowed_domains = None

        selector_hints: Optional[Mapping[str, Iterable[str]]] = getattr(
            self, "dynamic_selector_hints", None
        )
        if selector_hints:
            normalized_hints: dict[str, tuple[str, ...]] = {}
            for domain, hints in selector_hints.items():
                if not domain:
                    continue
                domain_key = domain.lower()
                if hints is None:
                    normalized_hints[domain_key] = tuple()
                    continue
                if isinstance(hints, str):
                    normalized_hints[domain_key] = (hints,)
                    continue

                normalized_tuple = tuple(hint for hint in hints if hint)
                normalized_hints[domain_key] = normalized_tuple
            self.dynamic_selector_hints = normalized_hints
        else:
            self.dynamic_selector_hints = {}

        compiled_filters = []
        for filt in self.path_filters:
            if isinstance(filt, str):
                compiled_filters.append(re.compile(filt))
            else:
                compiled_filters.append(filt)
        self.path_filters = compiled_filters

        normalized_exts = set()
        for ext in self.disallowed_extensions:
            if not ext:
                continue
            normalized_exts.add(ext if ext.startswith(".") else f".{ext}")
        self.disallowed_extensions = normalized_exts

        if self.allowed_query_params is not None:
            self.allowed_query_params = {param.lower() for param in self.allowed_query_params if param}
        else:
            self.allowed_query_params = None

        normalized_blocked_params = set()
        for param in self.blocked_query_params:
            if not param:
                continue
            normalized_blocked_params.add(param.lower())
        self.blocked_query_params = normalized_blocked_params


DEFAULT_TRACKING_QUERY_PARAMS = {
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
    "msclkid",
    "utm_campaign",
    "utm_content",
    "utm_id",
    "utm_medium",
    "utm_source",
    "utm_term",
}


class RateLimiter:
    """A simple asynchronous rate limiter.
    
    This class implements a rate limiter to control the frequency of requests,
    helping to be respectful to target websites and avoid overwhelming them.
    """
    def __init__(self, delay: Optional[float]):
        """Initialize the RateLimiter.

        Args:
            delay (Optional[float]): The minimum delay between operations in seconds.
                                   If None or <= 0, no rate limiting is applied.
        """
        self.delay = delay if delay and delay > 0 else None
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self):
        """Wait for the appropriate delay before allowing the next operation.
        
        This method ensures that operations are spaced out by at least the
        configured delay interval.
        """
        if not self.delay:
            return

        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            sleep_for = self.delay - (now - self._last)
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
                now = loop.time()
            self._last = now


def canonicalize_url(url: str, config: Optional[CrawlConfig] = None) -> Optional[str]:
    """Canonicalize a URL by normalizing its components.

    This function standardizes URLs by normalizing the scheme, domain, path,
    query parameters, and fragments according to the provided configuration.
    It helps avoid crawling duplicate content and maintains consistency.

    Args:
        url (str): The URL to canonicalize.
        config (Optional[CrawlConfig]): Configuration for URL canonicalization.

    Returns:
        Optional[str]: The canonicalized URL, or None if the URL is invalid.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    if parsed.scheme not in ("http", "https"):
        return None

    username = parsed.username or ""
    password = parsed.password or ""
    hostname = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        return None

    netloc = hostname
    if port:
        netloc = f"{netloc}:{port}"
    if username:
        auth = username
        if password:
            auth = f"{auth}:{password}"
        netloc = f"{auth}@{netloc}" if netloc else auth

    path = parsed.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    allowed_params = None
    blocked_params = set(DEFAULT_TRACKING_QUERY_PARAMS)
    strip_fragments = True

    if config:
        allowed_params = config.allowed_query_params
        blocked_params.update(config.blocked_query_params)
        strip_fragments = config.strip_empty_fragments

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()
        if allowed_params is not None and lower_key not in allowed_params:
            continue
        if lower_key in blocked_params or lower_key.startswith("utm_"):
            continue
        query_items.append((lower_key, value))

    query_items.sort()
    query = urlencode(query_items, doseq=True)

    fragment = ""
    if not strip_fragments and parsed.fragment:
        fragment = parsed.fragment

    normalized = parsed._replace(
        netloc=netloc,
        path=path,
        query=query,
        fragment=fragment,
    )
    return urlunparse(normalized)


def _is_allowed_by_config(url: str, config: CrawlConfig, root: Optional[str] = None) -> bool:
    """Check if a URL is allowed to be crawled based on the configuration.

    This function validates URLs against the crawl configuration to determine
    if they should be included in the crawl based on domain restrictions,
    file extensions, and path filters.

    Args:
        url (str): The URL to check.
        config (CrawlConfig): The crawl configuration containing restrictions.
        root (Optional[str]): The root URL of the crawl for special handling.

    Returns:
        bool: True if the URL is allowed to be crawled, False otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.netloc.lower()
    if config.allowed_domains is not None and hostname not in config.allowed_domains:
        return False

    if config.disallowed_extensions:
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in config.disallowed_extensions):
            return False

    if config.path_filters:
        path = parsed.path or "/"
        if root and url == root:
            return True
        if not any(f.search(path) for f in config.path_filters):
            return False

    return True


def _discover_sitemaps(html: str, base_url: str) -> list[str]:
    """Discover sitemap URLs from the HTML content of a page.

    This function searches for sitemap references in HTML content, including
    both explicit sitemap link tags and common sitemap locations.

    Args:
        html (str): The HTML content to search for sitemap references.
        base_url (str): The base URL to resolve relative sitemap URLs.

    Returns:
        list[str]: A list of discovered sitemap URLs.
    """
    sitemap_links = []
    for match in re.finditer(r'<link[^>]+rel=["\']sitemap["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        sitemap_links.append(urljoin(base_url, match.group(1)))
    sitemap_links.append(urljoin(base_url, "/sitemap.xml"))
    return sitemap_links


def _parse_sitemap_locations(xml_text: str) -> list[str]:
    """Parse location URLs from sitemap XML content.

    This function extracts all URL locations from a sitemap XML document,
    supporting both sitemap index files and URL sets.

    Args:
        xml_text (str): The XML content of the sitemap to parse.

    Returns:
        list[str]: A list of URLs found in the sitemap.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    locs = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            locs.append(elem.text.strip())
    return locs


async def crawl_site(
    root_url: str,
    timeout: int = 15,
    concurrency: int = 6,
    max_pages: int = 5,
    deep_contact: bool = True,
    config: Optional[CrawlConfig] = None,
):
    """Crawl a website starting from a root URL using BFS traversal.

    This function performs a comprehensive crawl of a website using a queue-based
    Breadth-First Search algorithm. It respects robots.txt rules, implements
    rate limiting, supports dynamic rendering for JavaScript-heavy sites,
    and prioritizes contact and about pages when deep_contact is enabled.

    The crawler maintains a cache of responses to avoid redundant requests and
    can handle both static HTML content and dynamically rendered JavaScript
    applications based on the configuration.

    Args:
        root_url (str): The URL to start crawling from.
        timeout (int): The timeout for HTTP requests in seconds. Defaults to 15.
        concurrency (int): The number of concurrent requests. Defaults to 6.
        max_pages (int): The maximum number of pages to crawl. Defaults to 5.
        deep_contact (bool): If True, prioritize crawling contact and about pages.
                           Defaults to True.
        config (Optional[CrawlConfig]): The crawl configuration. If None, uses
                                      default CrawlConfig settings.

    Returns:
        dict[str, str]: A dictionary mapping page URLs to their HTML content.

    Raises:
        ValueError: If max_depth is negative or root_url is invalid.
    """

    config = config or CrawlConfig()
    if config.max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    canonical_root = canonicalize_url(root_url, config)
    if not canonical_root:
        raise ValueError("Invalid root URL provided")

    if config.allowed_domains is None:
        config.allowed_domains = {urlparse(canonical_root).netloc.lower()}

    logger.info(
        "Starting crawl: %s (max_pages: %s, max_depth: %s, deep_contact: %s)",
        canonical_root,
        max_pages,
        config.max_depth,
        deep_contact,
    )

    pages: dict[str, str] = {}
    seen: set[str] = set()
    processed_sitemaps: set[str] = set()

    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    await queue.put((canonical_root, 0))
    seen.add(canonical_root)

    robots_delay = get_crawl_delay(canonical_root)
    effective_delay = config.request_delay or 0.0
    if robots_delay:
        effective_delay = max(effective_delay, robots_delay)
    rate_limiter = RateLimiter(effective_delay if effective_delay > 0 else None)

    sem = asyncio.Semaphore(max(1, concurrency))
    pages_lock = asyncio.Lock()
    seen_lock = asyncio.Lock()
    stop_event = asyncio.Event()
    sitemap_lock = asyncio.Lock()

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:

        async def fetch_with_cache(url: str) -> str:
            """Fetch a URL with caching support and optional dynamic rendering."""
            dynamic = _should_use_dynamic(url)
            cache_key = _cache_key(url, is_dynamic=dynamic)

            if config.use_cache:
                cached = read_cache(cache_key)
                if cached is not None:
                    return cached

            async with sem:
                await rate_limiter.wait()
                if dynamic:
                    hints = None
                    if config.dynamic_selector_hints:
                        hints = config.dynamic_selector_hints.get(
                            urlparse(url).netloc.lower()
                        )
                    html, _ = await fetch_dynamic(
                        url,
                        timeout=timeout,
                        selector_hints=hints,
                    )
                else:
                    html = await fetch_one(client, url, timeout=timeout)

            if html and config.use_cache:
                write_cache(cache_key, html)
            return html

        def _should_use_dynamic(target_url: str) -> bool:
            """Determine if a URL should use dynamic rendering."""
            if not config.dynamic_rendering:
                return False
            domain = urlparse(target_url).netloc.lower()
            if config.dynamic_allowed_domains is not None:
                return domain in config.dynamic_allowed_domains
            return True

        def _cache_key(target_url: str, *, is_dynamic: bool = False) -> str:
            """Generate a cache key for a URL, distinguishing dynamic content."""
            return f"dynamic::{target_url}" if is_dynamic else target_url

        async def enqueue_url(candidate: str, depth: int):
            """Add a URL to the crawl queue if it passes all validation checks."""
            if stop_event.is_set():
                return
            canonical = canonicalize_url(candidate, config)
            if not canonical or not _is_allowed_by_config(canonical, config, canonical_root):
                return
            if not robots_allowed(canonical):
                return
            async with seen_lock:
                if canonical in seen:
                    return
                seen.add(canonical)
            await queue.put((canonical, depth))

        async def process_sitemap(sitemap_url: str, current_depth: int):
            """Process a sitemap to extract and enqueue additional URLs."""
            canonical = canonicalize_url(sitemap_url, config)
            if not canonical:
                return

            async with sitemap_lock:
                if canonical in processed_sitemaps:
                    return
                processed_sitemaps.add(canonical)

            if not robots_allowed(canonical):
                return

            try:
                sitemap_body = await fetch_with_cache(canonical)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error fetching sitemap %s: %s", canonical, exc)
                return

            if not sitemap_body:
                return

            for loc in _parse_sitemap_locations(sitemap_body):
                loc_url = urljoin(canonical, loc)
                target_depth = current_depth + 1
                if target_depth > config.max_depth:
                    continue
                await enqueue_url(loc_url, target_depth)

        async def worker():
            """Worker coroutine that processes URLs from the crawl queue."""
            while True:
                item = await queue.get()
                if item is None:
                    queue.task_done()
                    break

                url, depth = item

                try:
                    if stop_event.is_set() or depth > config.max_depth:
                        continue

                    if not _is_allowed_by_config(url, config, canonical_root):
                        continue

                    if not robots_allowed(url):
                        continue

                    html = await fetch_with_cache(url)
                    if not html:
                        continue

                    added = False
                    async with pages_lock:
                        if url not in pages and len(pages) < max_pages:
                            pages[url] = html
                            added = True
                            if len(pages) >= max_pages:
                                stop_event.set()
                    if not added:
                        if stop_event.is_set():
                            continue

                    if depth == 0:
                        for sitemap in _discover_sitemaps(html, url):
                            await process_sitemap(sitemap, depth)

                    if depth < config.max_depth and not stop_event.is_set():
                        raw_links = extract_links(html, url)
                        joined_links = [urljoin(url, link) for link in raw_links]
                        prioritized = []
                        secondary = []
                        for link in joined_links:
                            if deep_contact and looks_contact_or_about(link):
                                prioritized.append(link)
                            else:
                                secondary.append(link)

                        for next_link in prioritized + secondary:
                            await enqueue_url(next_link, depth + 1)
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(max(1, concurrency))]
        await queue.join()
        for _ in workers:
            await queue.put(None)
        await asyncio.gather(*workers)

    logger.info("Crawl complete: %s total pages", len(pages))
    return pages