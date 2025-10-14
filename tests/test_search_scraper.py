import asyncio

from constants import MAX_NUM_SOURCES
from search_scraper import SearchScraper


def test_search_scraper_google_pagination_returns_requested_count(monkeypatch):
    requested_results = 35
    urls = [f"https://example{i}.com" for i in range(requested_results)]

    def fake_google_sites(query, max_results, api_key, cx):
        assert max_results == requested_results
        return urls

    async def fake_fetch_many(url_list, timeout, concurrency, use_cache):
        return {url: "<html><body>Test Content</body></html>" for url in url_list}

    monkeypatch.setattr("search_scraper.google_sites", fake_google_sites)
    monkeypatch.setattr("search_scraper.fetch_many", fake_fetch_many)

    scraper = SearchScraper(search_engine="google", google_api_key="key", google_cx="cx")
    result = asyncio.run(
        scraper.search_and_scrape("test query", num_results=requested_results, extraction_mode=False)
    )

    assert result.error is None
    assert len(result.sources) == requested_results
    assert result.markdown_content is not None


def test_search_scraper_clamps_to_max_sources(monkeypatch):
    captured_max = None

    def fake_google_sites(query, max_results, api_key, cx):
        nonlocal captured_max
        captured_max = max_results
        return [f"https://example{i}.com" for i in range(max_results)]

    async def fake_fetch_many(url_list, timeout, concurrency, use_cache):
        return {url: "<html><body>Content</body></html>" for url in url_list}

    monkeypatch.setattr("search_scraper.google_sites", fake_google_sites)
    monkeypatch.setattr("search_scraper.fetch_many", fake_fetch_many)

    scraper = SearchScraper(search_engine="google", google_api_key="key", google_cx="cx")
    result = asyncio.run(
        scraper.search_and_scrape("query", num_results=MAX_NUM_SOURCES + 10, extraction_mode=False)
    )

    assert captured_max == MAX_NUM_SOURCES
    assert len(result.sources) == MAX_NUM_SOURCES
    assert result.error is None
    assert result.markdown_content is not None
