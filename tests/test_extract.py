"""Tests for structured-data enhanced extraction."""

from __future__ import annotations

import textwrap

from extract import extract_basic


def _base_settings(**overrides):
    settings = {
        "extract_emails": False,
        "extract_phones": False,
        "extract_social": False,
        "extract_structured": True,
    }
    settings.update(overrides)
    return settings


def test_extract_basic_json_ld_contacts():
    html = textwrap.dedent(
        """
        <html>
          <head>
            <title>Schema Store</title>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "LocalBusiness",
              "name": "Schema Store",
              "email": "info@schemastore.example",
              "telephone": "+1-555-123-4567",
              "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 Schema St",
                "addressLocality": "Structured City",
                "addressRegion": "SC",
                "postalCode": "12345",
                "addressCountry": "US"
              },
              "sameAs": [
                "https://www.facebook.com/schema",
                "https://www.linkedin.com/company/schema"
              ],
              "contactPoint": [{
                "@type": "ContactPoint",
                "telephone": "+1-555-987-6543",
                "email": "sales@schemastore.example"
              }]
            }
            </script>
          </head>
          <body>
            <h1>Schema Store</h1>
          </body>
        </html>
        """
    )

    result = extract_basic("https://example.com", html, _base_settings())

    assert sorted(result["emails"]) == [
        "info@schemastore.example",
        "sales@schemastore.example",
    ]
    assert sorted(result["phones"]) == ["+1-555-123-4567", "+1-555-987-6543"]
    assert result["social"].get("facebook") == "https://www.facebook.com/schema"
    assert result["social"].get("linkedin") == "https://www.linkedin.com/company/schema"
    assert result["address"] and "123 Schema St" in result["address"]
    assert result["city"] == "Structured City"
    assert result["country"] == "US"


def test_extract_basic_microdata_contacts():
    html = textwrap.dedent(
        """
        <html>
          <head><title>Microdata Org</title></head>
          <body>
            <div itemscope itemtype="https://schema.org/Organization">
              <span itemprop="name">Microdata Org</span>
              <a itemprop="email" href="mailto:contact@micro.example">Email</a>
              <span itemprop="telephone">+44 20 7946 0958</span>
              <div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress">
                <span itemprop="streetAddress">1 Microdata Way</span>
                <span itemprop="addressLocality">London</span>
                <span itemprop="addressCountry">UK</span>
              </div>
              <a itemprop="sameAs" href="https://twitter.com/micro_org">Twitter</a>
            </div>
          </body>
        </html>
        """
    )

    result = extract_basic("https://micro.example", html, _base_settings())

    assert result["emails"] == ["contact@micro.example"]
    assert result["phones"] == ["+44 20 7946 0958"]
    assert result["social"].get("twitter") == "https://twitter.com/micro_org"
    assert result["address"] and "Microdata Way" in result["address"]
    assert result["city"] == "London"
    assert result["country"] == "UK"


def test_extract_basic_structured_toggle():
    html = """
    <html>
      <head>
        <script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","email":"toggle@example.com"}</script>
      </head>
      <body></body>
    </html>
    """

    disabled_settings = _base_settings(extract_structured=False)
    result = extract_basic("https://toggle.example", html, disabled_settings)
    assert result["emails"] == []

    enabled_settings = _base_settings()
    enabled_result = extract_basic("https://toggle.example", html, enabled_settings)
    assert enabled_result["emails"] == ["toggle@example.com"]
