"""Utilities for coordinating crawling/searching and aggregating contacts."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from crawl import crawl_site
from extract import extract_basic
from fetch import fetch_many
from logger import get_logger
from scrape_content import to_markdown
from search import ddg_sites

logger = get_logger(__name__)


@dataclass
class PageRecord:
    """Structured representation of a processed page."""

    url: str
    title: Optional[str]
    meta_description: Optional[str]
    markdown: str
    extraction: Dict

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "meta_description": self.meta_description,
            "markdown": self.markdown,
            "extraction": self.extraction,
        }


@dataclass
class PipelineResult:
    """Result of running the scraping pipeline."""

    seed: str
    mode: str
    pages: List[PageRecord] = field(default_factory=list)
    contacts: Dict[str, List[Dict[str, Iterable[str]]]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "seed": self.seed,
            "mode": self.mode,
            "pages": [page.to_dict() for page in self.pages],
            "contacts": self.contacts,
        }

    @property
    def page_count(self) -> int:
        return len(self.pages)


def _aggregate_contacts(pages: Iterable[PageRecord]) -> Dict[str, List[Dict[str, Iterable[str]]]]:
    email_sources: Dict[str, Set[str]] = {}
    phone_sources: Dict[str, Set[str]] = {}
    social_sources: Dict[Tuple[str, str], Set[str]] = {}

    for page in pages:
        extraction = page.extraction or {}

        for email in extraction.get("emails", []) or []:
            email_sources.setdefault(email, set()).add(page.url)

        for phone in extraction.get("phones", []) or []:
            phone_sources.setdefault(phone, set()).add(page.url)

        for network, link in (extraction.get("social", {}) or {}).items():
            if not link:
                continue
            social_sources.setdefault((network, link), set()).add(page.url)

    def _sorted_records(source_map: Dict[str, Set[str]], value_key: str) -> List[Dict[str, Iterable[str]]]:
        records = []
        for value, sources in sorted(source_map.items(), key=lambda item: item[0]):
            records.append({
                value_key: value,
                "sources": sorted(sources),
            })
        return records

    social_records = []
    for (network, link), sources in sorted(social_sources.items(), key=lambda item: (item[0][0], item[0][1])):
        social_records.append({
            "network": network,
            "url": link,
            "sources": sorted(sources),
        })

    return {
        "emails": _sorted_records(email_sources, "email"),
        "phones": _sorted_records(phone_sources, "phone"),
        "social": social_records,
    }


def build_pipeline_result(
    *,
    seed: str,
    mode: str,
    html_pages: Dict[str, str],
    extraction_settings: Optional[Dict] = None,
) -> PipelineResult:
    """Build a pipeline result from a mapping of URLs to HTML pages."""
    extraction_settings = extraction_settings or {}
    pages: List[PageRecord] = []

    for url, html in html_pages.items():
        if not html:
            logger.debug("Skipping empty HTML for %s", url)
            continue

        meta = to_markdown(html, include_meta=True)
        markdown = meta.get("markdown", "")
        title = meta.get("title")
        meta_description = meta.get("meta_description")

        extraction = extract_basic(url, html, extraction_settings)
        pages.append(
            PageRecord(
                url=url,
                title=title,
                meta_description=meta_description,
                markdown=markdown,
                extraction=extraction,
            )
        )

    contacts = _aggregate_contacts(pages)
    logger.info(
        "Pipeline aggregation complete for %s: %d pages, %d emails, %d phones, %d social",
        seed,
        len(pages),
        len(contacts.get("emails", [])),
        len(contacts.get("phones", [])),
        len(contacts.get("social", [])),
    )

    return PipelineResult(seed=seed, mode=mode, pages=pages, contacts=contacts)


async def run_site_pipeline(
    root_url: str,
    *,
    crawl_kwargs: Optional[Dict] = None,
    extraction_settings: Optional[Dict] = None,
) -> PipelineResult:
    """Run the pipeline on a website by crawling from the root URL."""
    crawl_kwargs = crawl_kwargs or {}
    pages = await crawl_site(root_url, **crawl_kwargs)
    return build_pipeline_result(
        seed=root_url,
        mode="crawl",
        html_pages=pages,
        extraction_settings=extraction_settings,
    )


async def run_search_pipeline(
    query: str,
    *,
    search_func: Callable[[str, int], List[str]] = ddg_sites,
    max_results: int = 5,
    fetch_kwargs: Optional[Dict] = None,
    extraction_settings: Optional[Dict] = None,
) -> PipelineResult:
    """Run the pipeline on search results returned by a search function."""
    fetch_kwargs = fetch_kwargs or {}
    urls = search_func(query, max_results)
    if not urls:
        logger.warning("No URLs returned for query: %s", query)
        return PipelineResult(
            seed=query,
            mode="search",
            pages=[],
            contacts=_aggregate_contacts([]),
        )

    html_pages = await fetch_many(urls, **fetch_kwargs)
    return build_pipeline_result(
        seed=query,
        mode="search",
        html_pages=html_pages,
        extraction_settings=extraction_settings,
    )


def run_site_pipeline_sync(
    root_url: str,
    *,
    crawl_kwargs: Optional[Dict] = None,
    extraction_settings: Optional[Dict] = None,
) -> PipelineResult:
    """Synchronous wrapper around :func:`run_site_pipeline`."""
    return asyncio.run(
        run_site_pipeline(
            root_url,
            crawl_kwargs=crawl_kwargs,
            extraction_settings=extraction_settings,
        )
    )


def run_search_pipeline_sync(
    query: str,
    *,
    search_func: Callable[[str, int], List[str]] = ddg_sites,
    max_results: int = 5,
    fetch_kwargs: Optional[Dict] = None,
    extraction_settings: Optional[Dict] = None,
) -> PipelineResult:
    """Synchronous wrapper around :func:`run_search_pipeline`."""
    return asyncio.run(
        run_search_pipeline(
            query,
            search_func=search_func,
            max_results=max_results,
            fetch_kwargs=fetch_kwargs,
            extraction_settings=extraction_settings,
        )
    )
