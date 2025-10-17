import httpx
from typing import List
from retry_utils import retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)


@retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
def google_sites(query: str, max_results: int, api_key: str, cx: str) -> List[str]:
    """Search the Google Custom Search API for a given query.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of results to return.
        api_key (str): Your Google API key.
        cx (str): Your Custom Search Engine ID.

    Returns:
        List[str]: A list of result URLs.
    """
    if not api_key or not cx:
        logger.warning("Google Custom Search API credentials not configured")
        return []

    logger.info(f"Searching Google CSE for: '{query}' (max_results: {max_results})")

    urls = []
    # Google returns 10 results per page
    remain = max_results
    start = 1

    while remain > 0 and start <= 91:  # API allows start 1..91
        num = min(10, remain)
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": num,
            "start": start,
        }

        try:
            logger.debug(f"Fetching page (start={start}, num={num})")
            r = httpx.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)

            if r.status_code == 429:
                logger.error("Rate limit exceeded for Google CSE API")
                break
            elif r.status_code != 200:
                logger.error(f"Google CSE API returned status {r.status_code}")
                break

            data = r.json()
            items = data.get("items") or []

            if not items:
                logger.debug("No more results available")
                break

            for it in items:
                link = it.get("link")
                if link and link.startswith("http"):
                    urls.append(link)

            logger.debug(f"Got {len(items)} results, total so far: {len(urls)}")

            start += num
            remain -= num

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Google CSE request: {e}")
            break
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during Google CSE request: {e}")
            break
        except Exception as e:
            logger.error(f"Error during Google CSE request: {e}")
            break

    # Deduplicate keeping order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)

    logger.info(f"Google CSE search complete: {len(out)} unique results")
    return out
