import asyncio
from types import SimpleNamespace

import site_extractor
from site_extractor import SiteExtractor


def test_extract_from_sitemap_is_async(monkeypatch):
    """Ensure sitemap downloads use the async client and execute concurrently."""

    extractor = SiteExtractor()

    sitemap_responses = {
        "https://example.com/sitemap-1.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <url><loc>https://example.com/page-1</loc></url>
            </urlset>
        """,
        "https://example.com/sitemap-2.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <url><loc>https://example.com/page-2</loc></url>
            </urlset>
        """,
    }

    call_log: list[tuple[str, str, float]] = []

    class DummyResponse:
        def __init__(self, body: str):
            self.content = body.encode("utf-8")

        def raise_for_status(self) -> None:  # pragma: no cover - no error path in test
            return None

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, **kwargs):
            loop = asyncio.get_running_loop()
            call_log.append(("start", url, loop.time()))
            await asyncio.sleep(0.1)
            call_log.append(("end", url, loop.time()))
            return DummyResponse(sitemap_responses[url])

    # Ensure robots.txt checks and downstream fetching don't hit the network
    monkeypatch.setattr(site_extractor, "robots_allowed", lambda url: True)
    monkeypatch.setattr(site_extractor, "httpx", SimpleNamespace(
        AsyncClient=DummyAsyncClient,
        HTTPError=Exception,
        TimeoutException=Exception,
    ))

    fetch_calls: list[tuple[str, ...]] = []

    async def fake_fetch_and_convert(self, urls):
        fetch_calls.append(tuple(urls))
        return {url: f"markdown:{url}" for url in urls}

    monkeypatch.setattr(SiteExtractor, "_fetch_and_convert", fake_fetch_and_convert)

    sitemap_urls = list(sitemap_responses.keys())
    async def run_test():
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        results = await asyncio.gather(
            *(extractor.extract_from_sitemap(url) for url in sitemap_urls)
        )
        elapsed = loop.time() - start_time

        start_events = [t for event, _, t in call_log if event == "start"]
        assert len(start_events) == len(sitemap_urls)
        # If the calls were sequential, the difference would be roughly 0.1s per sitemap
        assert max(start_events) - min(start_events) < 0.09
        # Both requests should complete in just over the single sleep
        assert elapsed < 0.18

        expected_pages = ["https://example.com/page-1", "https://example.com/page-2"]
        assert [tuple(urls) for urls in fetch_calls] == [(page,) for page in expected_pages]

        for result, page in zip(results, expected_pages):
            assert page in result
            assert result[page] == f"markdown:{page}"

    asyncio.run(run_test())
