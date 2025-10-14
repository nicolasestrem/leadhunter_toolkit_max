from scraping.pipeline import build_pipeline_result, run_search_pipeline_sync


def test_pipeline_aggregates_contacts_and_metadata():
    html_main = """
    <html>
      <head>
        <title>Example Inc.</title>
        <meta name="description" content="Quality services and products">
      </head>
      <body>
        <h1>Welcome to Example</h1>
        <p>Reach us at info@example.com or call +1 (555) 0100 for details.</p>
        <a href="https://twitter.com/example">Twitter</a>
      </body>
    </html>
    """

    html_contact = """
    <html>
      <head>
        <title>Contact Example</title>
        <meta property="og:description" content="Reach our team anytime">
      </head>
      <body>
        <p>Email support@example.com for help or info@example.com for sales.</p>
        <p>Phone: +1 (555) 0100</p>
        <a href="https://twitter.com/example">Follow us</a>
        <a href="https://www.linkedin.com/company/example">LinkedIn</a>
      </body>
    </html>
    """

    pages = {
        "https://example.com": html_main,
        "https://example.com/contact": html_contact,
    }

    result = build_pipeline_result(seed="https://example.com", mode="crawl", html_pages=pages)

    assert result.page_count == 2
    pages_by_url = {page.url: page for page in result.pages}
    assert pages_by_url["https://example.com"].title == "Example Inc."
    assert pages_by_url["https://example.com"].meta_description == "Quality services and products"
    assert "# Welcome to Example" in pages_by_url["https://example.com"].markdown

    emails = {entry["email"]: entry["sources"] for entry in result.contacts["emails"]}
    assert sorted(emails["info@example.com"]) == [
        "https://example.com",
        "https://example.com/contact",
    ]
    assert emails["support@example.com"] == ["https://example.com/contact"]

    phones = {entry["phone"]: entry["sources"] for entry in result.contacts["phones"]}
    assert phones["+1 (555) 0100"] == [
        "https://example.com",
        "https://example.com/contact",
    ]

    socials = {(entry["network"], entry["url"]): entry["sources"] for entry in result.contacts["social"]}
    assert socials[("twitter", "https://twitter.com/example")] == [
        "https://example.com",
        "https://example.com/contact",
    ]
    assert socials[("linkedin", "https://www.linkedin.com/company/example")] == [
        "https://example.com/contact",
    ]


def test_pipeline_handles_empty_pages():
    result = build_pipeline_result(seed="seed", mode="crawl", html_pages={"https://a": ""})
    assert result.page_count == 0
    assert result.contacts == {"emails": [], "phones": [], "social": []}


def _stubbed_page_outputs():
    return {
        "markdown": "",
        "title": None,
        "meta_description": None,
    }


def _stubbed_extraction():
    return {
        "emails": [],
        "phones": [],
        "social": {},
    }


def test_run_search_pipeline_uses_injected_callable(monkeypatch):
    def fake_ddg(*_args, **_kwargs):  # pragma: no cover - sanity guard
        raise AssertionError("ddg_sites should not be invoked when a search_func is provided")

    monkeypatch.setattr("scraping.pipeline.ddg_sites", fake_ddg)

    captured = {}

    def custom_search(query: str, max_results: int):
        captured["args"] = (query, max_results)
        return ["https://example.com"]

    async def fake_fetch_many(urls, **_kwargs):
        return {url: "<html></html>" for url in urls}

    monkeypatch.setattr("scraping.pipeline.fetch_many", fake_fetch_many)
    monkeypatch.setattr("scraping.pipeline.to_markdown", lambda *_args, **_kwargs: _stubbed_page_outputs())
    monkeypatch.setattr("scraping.pipeline.extract_basic", lambda *_args, **_kwargs: _stubbed_extraction())

    result = run_search_pipeline_sync(
        "b2b marketing contacts",
        search_func=custom_search,
        max_results=7,
        fetch_kwargs={"use_cache": False},
    )

    assert captured["args"] == ("b2b marketing contacts", 7)
    assert result.page_count == 1


def test_run_search_pipeline_passes_google_parameters(monkeypatch):
    def fake_ddg(*_args, **_kwargs):  # pragma: no cover - sanity guard
        raise AssertionError("DuckDuckGo fallback should not run when Google kwargs are supplied")

    monkeypatch.setattr("scraping.pipeline.ddg_sites", fake_ddg)

    captured = {}

    def fake_google(query: str, max_results: int, *, api_key: str, cx: str):
        captured["args"] = (query, max_results)
        captured["api_key"] = api_key
        captured["cx"] = cx
        return ["https://google-result.com"]

    async def fake_fetch_many(urls, **_kwargs):
        return {url: "<html></html>" for url in urls}

    monkeypatch.setattr("scraping.pipeline.google_sites", fake_google)
    monkeypatch.setattr("scraping.pipeline.fetch_many", fake_fetch_many)
    monkeypatch.setattr("scraping.pipeline.to_markdown", lambda *_args, **_kwargs: _stubbed_page_outputs())
    monkeypatch.setattr("scraping.pipeline.extract_basic", lambda *_args, **_kwargs: _stubbed_extraction())

    result = run_search_pipeline_sync(
        "contact discovery",
        google_kwargs={"api_key": "key-123", "cx": "cx-456"},
        max_results=4,
    )

    assert captured["args"] == ("contact discovery", 4)
    assert captured["api_key"] == "key-123"
    assert captured["cx"] == "cx-456"
    assert result.page_count == 1
