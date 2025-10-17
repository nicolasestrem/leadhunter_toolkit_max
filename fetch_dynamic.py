"""Utilities for fetching dynamic web pages using Playwright."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Iterable, Optional, Tuple, Dict, Any

from logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def _playwright_browser():
    """Context manager to lazily import Playwright and launch Chromium.
    
    This function provides a context manager that imports Playwright on demand
    and launches a Chromium browser instance for dynamic content rendering.
    
    Yields:
        Browser context object for creating pages and navigating to URLs.
        
    Raises:
        RuntimeError: If Playwright is not installed or cannot be imported.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - exercised in smoke tests
        raise RuntimeError(
            "Playwright is required for dynamic rendering. Install it with"
            " `pip install playwright` and run `playwright install chromium`."
        ) from exc

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            try:
                yield context
            finally:
                await context.close()
        finally:
            await browser.close()


async def fetch_dynamic(
    url: str,
    *,
    timeout: int = 30,
    selector_hints: Optional[Iterable[str]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Fetch a URL using Playwright with optional selector hints.

    This function uses Playwright to render JavaScript-heavy web pages and
    extract their final HTML content after dynamic loading is complete.
    It supports selector hints to wait for specific elements to appear,
    indicating that the page has finished loading dynamic content.

    Args:
        url (str): Target URL to render.
        timeout (int): Overall timeout in seconds for navigation and wait conditions.
                      Defaults to 30 seconds.
        selector_hints (Optional[Iterable[str]]): Optional CSS selectors that hint 
                                                 when the page is "ready". The first
                                                 selector that becomes visible will
                                                 end the wait early.

    Returns:
        Tuple[str, Dict[str, Any]]: A tuple containing the final HTML string and 
                                   a metadata dictionary with navigation information
                                   including requested_url, final_url, status, and
                                   any error information.
    """

    metadata: Dict[str, Any] = {
        "requested_url": url,
        "final_url": None,
        "status": None,
    }

    try:
        async with _playwright_browser() as context:
            page = await context.new_page()
            logger.debug("[dynamic] Navigating to %s", url)
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=timeout * 1000,
            )

            if selector_hints:
                from playwright.async_api import TimeoutError as PlaywrightTimeoutError

                for selector in selector_hints:
                    try:
                        await page.wait_for_selector(
                            selector,
                            timeout=timeout * 1000,
                        )
                        break
                    except PlaywrightTimeoutError:
                        logger.debug(
                            "[dynamic] Selector hint %s not found for %s", selector, url
                        )
                else:
                    logger.debug(
                        "[dynamic] No selector hints matched for %s; falling back to network idle.",
                        url,
                    )
                    await _wait_for_network_idle(page, timeout)
            else:
                await _wait_for_network_idle(page, timeout)

            html = await page.content()
            if response is not None:
                metadata["status"] = response.status
                metadata["final_url"] = response.url
            else:
                metadata["final_url"] = page.url

            logger.info("[dynamic] Fetched %s (%s chars)", metadata["final_url"], len(html))
            return html, metadata
    except Exception as exc:
        metadata["error"] = str(exc)
        logger.error("Dynamic fetch failed for %s: %s", url, exc)
        return "", metadata


async def _wait_for_network_idle(page, timeout: int) -> None:
    """Wait for the network to go idle, swallowing timeout errors.
    
    This helper function waits for network activity to settle, indicating
    that dynamic content loading is likely complete. It gracefully handles
    timeout errors to avoid breaking the overall fetch operation.
    
    Args:
        page: Playwright page object to monitor for network idle state.
        timeout (int): Maximum time to wait for network idle in seconds.
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    try:
        await page.wait_for_load_state("networkidle", timeout=timeout * 1000)
    except PlaywrightTimeoutError:
        logger.debug("[dynamic] Network idle wait timed out")


__all__ = ["fetch_dynamic"]