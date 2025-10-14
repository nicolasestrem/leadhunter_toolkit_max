from scraping.pipeline import build_pipeline_result


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
