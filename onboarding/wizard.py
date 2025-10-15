"""
Onboarding wizard
Automates client onboarding with site crawl, audit, and quick wins generation
"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from crawl import crawl_site
from fetch import fetch_many
from audit.page_audit import audit_page, PageAudit
from audit.quick_wins import generate_quick_wins, export_quick_wins_markdown, PrioritizedTask
from llm.adapter import LLMAdapter
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class OnboardingResult:
    """Result of onboarding process"""
    domain: str
    pages_crawled: int
    pages_audited: int
    audits: List[PageAudit]
    all_quick_wins: List[PrioritizedTask]
    generated_at: datetime
    output_file: Optional[Path] = None
    failed_urls: List[str] = field(default_factory=list)


def select_key_pages(
    crawled_urls: List[str],
    max_pages: int = 3
) -> List[str]:
    """
    Select key pages to audit from crawled URLs

    Prioritizes:
    1. Homepage
    2. About page
    3. Contact page
    4. Services/Products pages

    Args:
        crawled_urls: List of crawled URLs
        max_pages: Maximum pages to audit

    Returns:
        List of selected URLs
    """
    if not crawled_urls:
        return []

    priority_keywords = [
        ['/', 'index', 'home'],  # Homepage
        ['about', 'ueber-uns', 'a-propos'],  # About
        ['contact', 'kontakt'],  # Contact
        ['services', 'products', 'leistungen', 'produkte'],  # Services/Products
    ]

    selected = []
    remaining = list(crawled_urls)

    # First pass: exact matches by priority
    for keywords in priority_keywords:
        if len(selected) >= max_pages:
            break

        for url in remaining:
            url_lower = url.lower()

            # Check if URL matches any keyword
            if any(keyword in url_lower for keyword in keywords):
                selected.append(url)
                remaining.remove(url)
                break

    # Second pass: fill remaining slots with any pages
    while len(selected) < max_pages and remaining:
        selected.append(remaining.pop(0))

    return selected[:max_pages]


async def run_onboarding(
    domain: str,
    llm_adapter: LLMAdapter,
    max_crawl_pages: int = 10,
    max_audit_pages: int = 3,
    output_dir: Optional[Path] = None,
    concurrency: int = 5
) -> OnboardingResult:
    """
    Run automated onboarding process

    Workflow:
    1. Crawl site (max_crawl_pages)
    2. Select key pages (max_audit_pages)
    3. Audit each key page with LLM
    4. Generate aggregated quick wins
    5. Export to markdown

    Args:
        domain: Domain to onboard (e.g., "example.com")
        llm_adapter: Configured LLM adapter
        max_crawl_pages: Max pages to crawl
        max_audit_pages: Max pages to audit in detail
        output_dir: Optional output directory
        concurrency: Concurrent requests

    Returns:
        OnboardingResult
    """
    logger.info(f"Starting onboarding for {domain}")

    # Ensure domain has protocol
    if not domain.startswith('http'):
        base_url = f"https://{domain}"
    else:
        base_url = domain

    # Step 1: Crawl site
    logger.info(f"Crawling {base_url} (max {max_crawl_pages} pages)")
    crawled_urls = await crawl_site(
        base_url,
        max_pages=max_crawl_pages,
        concurrency=concurrency
    )

    logger.info(f"Crawled {len(crawled_urls)} pages")

    if not crawled_urls:
        logger.warning("No pages crawled, returning empty result")
        return OnboardingResult(
            domain=domain,
            pages_crawled=0,
            pages_audited=0,
            audits=[],
            all_quick_wins=[],
            generated_at=datetime.now(),
            failed_urls=[]
        )

    # Step 2: Select key pages
    key_urls = select_key_pages(crawled_urls, max_audit_pages)
    logger.info(f"Selected {len(key_urls)} key pages for audit")

    # Step 3: Fetch HTML content for key pages
    logger.info(f"Fetching HTML for {len(key_urls)} pages")
    html_results = await fetch_many(key_urls, concurrency=concurrency)

    # Step 4: Audit each page
    audits = []
    failed_urls: List[str] = []
    for url in key_urls:
        html_content = html_results.get(url, '')

        if not html_content:
            logger.warning(f"No HTML content for {url}, skipping audit")
            failed_urls.append(url)
            continue

        logger.info(f"Auditing {url}")
        try:
            audit = audit_page(
                url=url,
                html_content=html_content,
                llm_adapter=llm_adapter,
                use_llm=True
            )
        except Exception as exc:  # noqa: BLE001 - Surface audit errors gracefully
            logger.error(f"Audit failed for {url}: {exc}", exc_info=True)
            failed_urls.append(url)
            continue

        audits.append(audit)

    logger.info(f"Completed {len(audits)} page audits")
    if failed_urls:
        logger.warning(f"Failed to audit {len(failed_urls)} pages: {failed_urls}")

    # Step 5: Aggregate quick wins from all audits
    all_tasks = []
    for audit in audits:
        tasks = generate_quick_wins(audit, max_wins=5, include_llm_wins=True)
        all_tasks.extend(tasks)

    # Deduplicate and re-prioritize
    seen_titles = set()
    unique_tasks = []
    for task in sorted(all_tasks, key=lambda x: x.priority_score, reverse=True):
        if task.task.title not in seen_titles:
            seen_titles.add(task.task.title)
            unique_tasks.append(task)

    # Take top tasks
    top_tasks = unique_tasks[:8]

    logger.info(f"Generated {len(top_tasks)} aggregated quick wins")

    # Create result
    result = OnboardingResult(
        domain=domain,
        pages_crawled=len(crawled_urls),
        pages_audited=len(audits),
        audits=audits,
        all_quick_wins=top_tasks,
        generated_at=datetime.now(),
        failed_urls=failed_urls
    )

    # Step 6: Export to markdown if output_dir provided
    if output_dir and top_tasks:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create slug from domain
        slug = domain.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')

        # Generate markdown
        md_content = f"# Onboarding Quick Wins: {domain}\n\n"
        md_content += f"**Generated**: {result.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        md_content += f"**Pages Crawled**: {result.pages_crawled}\n"
        md_content += f"**Pages Audited**: {result.pages_audited}\n\n"
        md_content += "---\n\n"

        # Add audit summaries
        md_content += "## Audit Summary\n\n"
        for audit in audits:
            md_content += f"### {audit.url}\n\n"
            md_content += f"- **Score**: {audit.score}/100 (Grade {audit.grade})\n"
            md_content += f"- **Content**: {audit.content_score}/100\n"
            md_content += f"- **Technical**: {audit.technical_score}/100\n"
            md_content += f"- **SEO**: {audit.seo_score}/100\n"
            md_content += f"- **Issues**: {len(audit.issues)}\n\n"

        md_content += "---\n\n"

        # Add quick wins
        md_content += export_quick_wins_markdown(top_tasks, base_url, domain)

        # Save file
        timestamp = result.generated_at.strftime('%Y%m%d_%H%M%S')
        filename = f"{slug}_onboarding_{timestamp}.md"
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        result.output_file = filepath
        logger.info(f"Saved onboarding report to {filepath}")

    return result
