"""Tests for dynamic rendering helpers and integration points."""

import asyncio
import http.server
import socket
import threading
from contextlib import closing

import pytest

import crawl
import fetch
from crawl import CrawlConfig
from fetch_dynamic import fetch_dynamic


def test_fetch_many_dynamic_uses_cache(monkeypatch):
    store: dict[str, str] = {}

    monkeypatch.setattr(fetch, "read_cache", lambda key: store.get(key))

    def fake_write_cache(key: str, value: str) -> bool:
        store[key] = value
        return True

    async def fake_fetch_one(*args, **kwargs):  # pragma: no cover - safety
        raise AssertionError("HTTP fetch should not be used during dynamic test")

    async def fake_fetch_dynamic(url: str, *, timeout: int, selector_hints=None):
        return "<html id='app'>dynamic</html>", {"status": 200, "final_url": url}

    monkeypatch.setattr(fetch, "write_cache", fake_write_cache)
    monkeypatch.setattr(fetch, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(fetch, "fetch_dynamic", fake_fetch_dynamic)

    urls = ["https://example.com"]

    result = asyncio.run(
        fetch.fetch_many(
            urls,
            timeout=5,
            concurrency=1,
            use_cache=True,
            dynamic_rendering=True,
            dynamic_allowlist={"example.com"},
            dynamic_selector_hints={"example.com": ["#app"]},
        )
    )

    assert result[urls[0]] == "<html id='app'>dynamic</html>"
    assert store["dynamic::https://example.com"] == "<html id='app'>dynamic</html>"

    # Second invocation should hit the cache and avoid calling fetch_dynamic again
    call_counter = {"count": 0}

    async def counting_fetch_dynamic(url: str, *, timeout: int, selector_hints=None):
        call_counter["count"] += 1
        return "<html id='app'>dynamic</html>", {"status": 200, "final_url": url}

    monkeypatch.setattr(fetch, "fetch_dynamic", counting_fetch_dynamic)

    result_cached = asyncio.run(
        fetch.fetch_many(
            urls,
            timeout=5,
            concurrency=1,
            use_cache=True,
            dynamic_rendering=True,
            dynamic_allowlist={"example.com"},
        )
    )

    assert result_cached[urls[0]] == "<html id='app'>dynamic</html>"
    assert call_counter["count"] == 0


def test_crawl_site_dynamic_fetch(monkeypatch):
    store: dict[str, str] = {}

    monkeypatch.setattr("crawl.read_cache", lambda key: store.get(key))

    def fake_write_cache(key: str, value: str) -> bool:
        store[key] = value
        return True

    async def fake_dynamic(url: str, *, timeout: int):
        return "<html><body><a href='https://example.com/about'>About</a></body></html>", {
            "status": 200,
            "final_url": url,
        }

    async def fake_fetch_one(*args, **kwargs):  # pragma: no cover - safety
        raise AssertionError("Static fetch should be bypassed when dynamic rendering is enabled")

    monkeypatch.setattr("crawl.write_cache", fake_write_cache)
    monkeypatch.setattr("crawl.fetch_dynamic", fake_dynamic)
    monkeypatch.setattr("crawl.fetch_one", fake_fetch_one)
    monkeypatch.setattr("crawl.robots_allowed", lambda url: True)
    monkeypatch.setattr("crawl.get_crawl_delay", lambda url: None)

    pages = asyncio.run(
        crawl.crawl_site(
            "https://example.com",
            max_pages=1,
            config=CrawlConfig(
                max_depth=0,
                use_cache=True,
                dynamic_rendering=True,
                dynamic_allowed_domains={"example.com"},
            ),
        )
    )

    assert any(key.startswith("https://example.com") for key in pages)
    assert any(key.startswith("dynamic::https://example.com") for key in store)
    assert next(iter(store.values())) == next(iter(pages.values()))


PLAYWRIGHT_MARK = pytest.mark.playwright


@PLAYWRIGHT_MARK
def test_fetch_dynamic_smoke():
    pytest.importorskip("playwright.async_api")

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # pragma: no cover - exercised in smoke test
            body = (
                "<html><body><div id='content'>Loading...</div>"
                "<script>document.getElementById('content').textContent='Dynamic Content';</script>"
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A003
            return

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        html, metadata = asyncio.run(
            fetch_dynamic(
                f"http://127.0.0.1:{port}",
                timeout=10,
                selector_hints=["#content"],
            )
        )
    finally:
        server.shutdown()
        thread.join()

    assert "Dynamic Content" in html
    assert metadata["status"] == 200
