import asyncio
from collections import Counter

import pytest

import crawl


def test_crawl_deduplicates_and_respects_depth(monkeypatch):
    html_map = {
        "http://example.com/": (
            '<html><head><link rel="sitemap" href="/sitemap.xml" /></head>'
            '<body>'
            '<a href="/about">About</a>'
            '<a href="/contact#top">Contact</a>'
            '<a href="/level1/page/">Level1</a>'
            '<a href="/blocked">Blocked</a>'
            '</body></html>'
        ),
        "http://example.com/about": '<a href="/level2/deep">Deep</a>',
        "http://example.com/contact": "<p>Contact</p>",
        "http://example.com/level1/page": '<a href="/level2/deep/">Deep</a>',
        "http://example.com/level2/deep": "<p>Deep</p>",
        "http://example.com/sitemap.xml": (
            "<urlset><url><loc>http://example.com/sitemap-page/</loc></url></urlset>"
        ),
        "http://example.com/sitemap-page": "<p>From sitemap</p>",
    }

    robots_rules = {
        "http://example.com/": True,
        "http://example.com/about": True,
        "http://example.com/contact": True,
        "http://example.com/level1/page": True,
        "http://example.com/level2/deep": True,
        "http://example.com/sitemap.xml": True,
        "http://example.com/sitemap-page": True,
        "http://example.com/blocked": False,
    }

    fetch_calls = []

    async def fake_fetch_one(client, url, timeout=15):
        fetch_calls.append(url)
        return html_map.get(url, "")

    monkeypatch.setattr(crawl, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(crawl, "robots_allowed", lambda url: robots_rules.get(url, True))
    monkeypatch.setattr(crawl, "get_crawl_delay", lambda url: 0)

    config = crawl.CrawlConfig(max_depth=1, use_cache=False)

    pages = asyncio.run(
        crawl.crawl_site(
        "http://example.com/#ignored",
        max_pages=5,
        concurrency=2,
        config=config,
        )
    )

    assert set(pages.keys()) == {
        "http://example.com/",
        "http://example.com/about",
        "http://example.com/contact",
        "http://example.com/level1/page",
        "http://example.com/sitemap-page",
    }
    assert "http://example.com/level2/deep" not in pages
    assert "http://example.com/blocked" not in pages
    assert all("#" not in url for url in fetch_calls)
    assert Counter(fetch_calls)["http://example.com/contact"] == 1


def test_crawl_respects_filters(monkeypatch):
    html_map = {
        "http://example.com/": (
            '<a href="/keep/">Keep</a>'
            '<a href="/skip.pdf">Skip</a>'
            '<a href="/deep/page">Deep</a>'
            '<a href="http://external.com/path">External</a>'
        ),
        "http://example.com/keep": "<p>Keep</p><a href=\"/deep/page\">Deep</a>",
        "http://example.com/deep/page": "<p>Deep</p>",
    }

    fetch_calls = []

    async def fake_fetch_one(client, url, timeout=15):
        fetch_calls.append(url)
        return html_map.get(url, "")

    monkeypatch.setattr(crawl, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(crawl, "robots_allowed", lambda url: True)
    monkeypatch.setattr(crawl, "get_crawl_delay", lambda url: 0)

    config = crawl.CrawlConfig(
        max_depth=2,
        path_filters=[r"^/keep"],
        disallowed_extensions={".pdf"},
        use_cache=False,
    )

    pages = asyncio.run(
        crawl.crawl_site(
        "http://example.com/",
        max_pages=4,
        concurrency=2,
        config=config,
        )
    )

    assert set(pages.keys()) == {"http://example.com/", "http://example.com/keep"}
    assert "http://example.com/deep/page" not in pages
    assert all(not url.startswith("http://external.com") for url in fetch_calls)


def test_crawl_normalizes_tracking_query_params(monkeypatch):
    html_map = {
        "http://example.com/": "<a>Root</a>",
        "http://example.com/?id=123": "<p>Page</p>",
    }

    fetch_calls = []

    async def fake_fetch_one(client, url, timeout=15):
        fetch_calls.append(url)
        return html_map.get(url, "")

    def fake_extract_links(html, base_url):
        return [
            "http://example.com/?id=123&utm_source=Google",
            "http://example.com/?utm_medium=email&id=123",
            "http://example.com/?id=123&fbclid=abc",
            "http://example.com/?utm_campaign=sale&id=123&utm_term=deal",
        ]

    monkeypatch.setattr(crawl, "extract_links", fake_extract_links)
    monkeypatch.setattr(crawl, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(crawl, "robots_allowed", lambda url: True)
    monkeypatch.setattr(crawl, "get_crawl_delay", lambda url: 0)

    config = crawl.CrawlConfig(max_depth=1, use_cache=False)

    pages = asyncio.run(
        crawl.crawl_site(
            "http://example.com/?utm_content=ignore#frag",
            max_pages=3,
            concurrency=1,
            config=config,
        )
    )

    assert set(pages.keys()) == {"http://example.com/", "http://example.com/?id=123"}
    assert Counter(fetch_calls)["http://example.com/?id=123"] == 1
    assert all("utm" not in url and "fbclid" not in url for url in fetch_calls)


def test_canonicalize_url_skips_invalid_ports():
    config = crawl.CrawlConfig()
    assert crawl.canonicalize_url("http://example.com:abc", config) is None
    assert crawl.canonicalize_url("https://example.com:999999", config) is None
