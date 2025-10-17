import urllib.robotparser as urp
import httpx
from urllib.parse import urlparse
from typing import Optional

USER_AGENT = "LeadHunter/1.0"

_cache = {}


def _base_url(url: str) -> Optional[str]:
    """Get the base URL (scheme and netloc) from a full URL.

    Args:
        url (str): The URL to parse.

    Returns:
        Optional[str]: The base URL, or None if the URL is invalid.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}"
    except (ValueError, AttributeError):
        return None


def get_robots_parser(url: str) -> Optional[urp.RobotFileParser]:
    """Get a robots.txt parser for a given URL.

    This function fetches and parses the robots.txt file for a domain, with in-memory
    caching to avoid redundant requests.

    Args:
        url (str): The URL of the site to get the parser for.

    Returns:
        Optional[urp.RobotFileParser]: The parser object, or None if the URL is invalid.
    """
    base = _base_url(url)
    if not base:
        return None

    if base in _cache:
        return _cache[base]

    robots_url = base + "/robots.txt"
    rp = urp.RobotFileParser()
    try:
        r = httpx.get(robots_url, timeout=10, headers={"User-Agent": USER_AGENT})
        if r.status_code >= 400:
            rp.parse([])
        else:
            rp.parse(r.text.splitlines())
    except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
        rp.parse([])
    rp.set_url(robots_url)
    _cache[base] = rp
    return rp

def robots_allowed(url: str) -> bool:
    """Check if a URL is allowed to be crawled according to robots.txt.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if crawling is allowed, False otherwise.
    """
    try:
        parser = get_robots_parser(url)
        if not parser:
            return True
        return parser.can_fetch(USER_AGENT, url)
    except (ValueError, AttributeError):
        # Invalid URL or parsing error - allow crawling by default
        return True


def get_crawl_delay(url: str, user_agent: str = USER_AGENT) -> Optional[float]:
    """Get the crawl delay specified in the robots.txt file.

    Args:
        url (str): The URL of the site.
        user_agent (str): The user agent to check the delay for.

    Returns:
        Optional[float]: The crawl delay in seconds, or None if not specified.
    """
    parser = get_robots_parser(url)
    if not parser:
        return None

    delay = parser.crawl_delay(user_agent)
    if delay is None:
        delay = parser.crawl_delay("*")
    return delay
