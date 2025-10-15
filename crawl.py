import asyncio
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterable, Optional
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
    dynamic_rendering: bool = False
    dynamic_allowed_domains: Optional[Iterable[str]] = None

    def __post_init__(self):
        if self.allowed_domains is not None:
            self.allowed_domains = {d.lower() for d in self.allowed_domains}
        else:
            self.allowed_domains = None

        if self.dynamic_allowed_domains is not None:
            self.dynamic_allowed_domains = {
                d.lower() for d in self.dynamic_allowed_domains
            }
        else:
            self.dynamic_allowed_domains = None

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
    def __init__(self, delay: Optional[float]):
        self.delay = delay if delay and delay > 0 else None
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def wait(self):
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
    sitemap_links = []
    for match in re.finditer(r'<link[^>]+rel=["\']sitemap["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        sitemap_links.append(urljoin(base_url, match.group(1)))
    sitemap_links.append(urljoin(base_url, "/sitemap.xml"))
    return sitemap_links


def _parse_sitemap_locations(xml_text: str) -> list[str]:
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
    """Crawl a website starting from root URL using a queue-based BFS."""

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
            dynamic = _should_use_dynamic(url)
            cache_key = _cache_key(url, is_dynamic=dynamic)

            if config.use_cache:
                cached = read_cache(cache_key)
                if cached is not None:
                    return cached

            async with sem:
                await rate_limiter.wait()
                if dynamic:
                    html, _ = await fetch_dynamic(url, timeout=timeout)
                else:
                    html = await fetch_one(client, url, timeout=timeout)

            if html and config.use_cache:
                write_cache(cache_key, html)
            return html

        def _should_use_dynamic(target_url: str) -> bool:
            if not config.dynamic_rendering:
                return False
            domain = urlparse(target_url).netloc.lower()
            if config.dynamic_allowed_domains is not None:
                return domain in config.dynamic_allowed_domains
            return True

        def _cache_key(target_url: str, *, is_dynamic: bool = False) -> str:
            return f"dynamic::{target_url}" if is_dynamic else target_url

        async def enqueue_url(candidate: str, depth: int):
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
