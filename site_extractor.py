"""
Site Extractor - Convert entire websites or sitemaps to markdown
"""
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urlparse
import re
from markdownify import markdownify as md
from fetch import fetch_many
from crawl import crawl_site
from robots_util import robots_allowed
from logger import get_logger

logger = get_logger(__name__)

OUT_DIR = Path(__file__).parent / "out"
OUT_DIR.mkdir(exist_ok=True)


class SiteExtractor:
    """Extract and convert entire websites to markdown"""

    def __init__(self, timeout: int = 15, concurrency: int = 6):
        """
        Initialize site extractor

        Args:
            timeout: HTTP request timeout in seconds
            concurrency: Number of concurrent requests
        """
        self.timeout = timeout
        self.concurrency = concurrency

    async def extract_from_sitemap(
        self,
        sitemap_url: str,
        max_pages: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Extract all pages from a sitemap.xml

        Args:
            sitemap_url: URL to sitemap.xml
            max_pages: Optional limit on number of pages

        Returns:
            Dictionary of {url: markdown_content}
        """
        logger.info(f"Fetching sitemap: {sitemap_url}")

        try:
            # Fetch sitemap
            import httpx
            resp = httpx.get(sitemap_url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()

            # Parse XML
            root = ET.fromstring(resp.content)

            # Extract URLs (handle namespace)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = []

            for url_elem in root.findall('.//ns:url/ns:loc', namespaces):
                url = url_elem.text
                if url and robots_allowed(url):
                    urls.append(url)

            # If sitemap index, recursively fetch sub-sitemaps
            if not urls:
                for sitemap_elem in root.findall('.//ns:sitemap/ns:loc', namespaces):
                    sub_sitemap_url = sitemap_elem.text
                    if sub_sitemap_url:
                        logger.info(f"Found sub-sitemap: {sub_sitemap_url}")
                        sub_urls = await self.extract_from_sitemap(sub_sitemap_url, max_pages)
                        urls.extend(sub_urls.keys())

            if max_pages:
                urls = urls[:max_pages]

            logger.info(f"Found {len(urls)} URLs in sitemap")

            # Fetch and convert to markdown
            return await self._fetch_and_convert(urls)

        except Exception as e:
            logger.error(f"Error extracting from sitemap {sitemap_url}: {e}")
            return {}

    async def extract_from_domain(
        self,
        domain_url: str,
        max_pages: int = 50,
        deep_crawl: bool = True
    ) -> Dict[str, str]:
        """
        Extract pages from a domain via crawling

        Args:
            domain_url: Starting URL (domain homepage)
            max_pages: Maximum pages to crawl
            deep_crawl: Whether to deep crawl

        Returns:
            Dictionary of {url: markdown_content}
        """
        logger.info(f"Crawling domain: {domain_url}")

        try:
            # Use existing crawler
            pages_html = await crawl_site(
                domain_url,
                timeout=self.timeout,
                concurrency=self.concurrency,
                max_pages=max_pages,
                deep_contact=deep_crawl
            )

            logger.info(f"Crawled {len(pages_html)} pages")

            # Convert to markdown
            pages_md = {}
            for url, html in pages_html.items():
                if html:
                    pages_md[url] = self._html_to_markdown(html)

            return pages_md

        except Exception as e:
            logger.error(f"Error extracting from domain {domain_url}: {e}")
            return {}

    async def _fetch_and_convert(self, urls: List[str]) -> Dict[str, str]:
        """Fetch URLs and convert to markdown"""
        logger.info(f"Fetching {len(urls)} pages...")

        # Fetch all pages
        pages_html = await fetch_many(
            urls,
            timeout=self.timeout,
            concurrency=self.concurrency,
            use_cache=True
        )

        # Convert to markdown
        pages_md = {}
        for url, html in pages_html.items():
            if html:
                pages_md[url] = self._html_to_markdown(html)

        logger.info(f"Converted {len(pages_md)} pages to markdown")
        return pages_md

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to clean markdown"""
        if not html:
            return ""

        try:
            markdown = md(
                html,
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav'],
                escape_asterisks=False,
                escape_underscores=False
            )

            # Clean up excessive whitespace
            lines = [line.rstrip() for line in markdown.split('\n')]
            # Remove excessive blank lines (max 2 consecutive)
            cleaned_lines = []
            blank_count = 0

            for line in lines:
                if line.strip():
                    cleaned_lines.append(line)
                    blank_count = 0
                else:
                    blank_count += 1
                    if blank_count <= 2:
                        cleaned_lines.append(line)

            return '\n'.join(cleaned_lines)

        except Exception as e:
            logger.error(f"Error converting HTML to markdown: {e}")
            return ""

    def _sanitize_filename(self, url: str) -> str:
        """Create safe filename from URL"""
        # Get path component
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if not path:
            return "index"

        # Remove file extension if present
        path = re.sub(r'\.(html?|php|asp|jsp)$', '', path, flags=re.IGNORECASE)

        # Replace path separators and special chars
        safe_name = re.sub(r'[^\w\-]', '_', path)

        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        return safe_name or "page"

    def save_to_files(
        self,
        pages: Dict[str, str],
        domain_name: str,
        create_combined: bool = True
    ) -> Path:
        """
        Save extracted pages to individual markdown files

        Args:
            pages: Dictionary of {url: markdown_content}
            domain_name: Name of the domain (for directory name)
            create_combined: Whether to create a combined markdown file

        Returns:
            Path to output directory
        """
        # Create output directory
        safe_domain = re.sub(r'[^\w\-]', '_', domain_name)
        output_dir = OUT_DIR / f"site_{safe_domain}"
        output_dir.mkdir(exist_ok=True)

        logger.info(f"Saving {len(pages)} pages to {output_dir}")

        # Save individual files
        for url, content in pages.items():
            filename = self._sanitize_filename(url) + ".md"
            filepath = output_dir / filename

            try:
                # Add metadata header
                metadata = f"""---
URL: {url}
Extracted: {Path(__file__).name}
---

"""
                full_content = metadata + content

                filepath.write_text(full_content, encoding="utf-8")
                logger.debug(f"Saved: {filepath.name}")

            except Exception as e:
                logger.error(f"Error saving {url} to {filepath}: {e}")

        # Create combined file
        if create_combined:
            combined_path = output_dir / "_combined.md"
            try:
                combined_content = []

                combined_content.append(f"# {domain_name} - Complete Site Export\n\n")
                combined_content.append(f"Total pages: {len(pages)}\n\n")
                combined_content.append("---\n\n")

                for url, content in pages.items():
                    combined_content.append(f"# {url}\n\n")
                    combined_content.append(content)
                    combined_content.append("\n\n" + "="*80 + "\n\n")

                combined_path.write_text("".join(combined_content), encoding="utf-8")
                logger.info(f"Created combined file: {combined_path}")

            except Exception as e:
                logger.error(f"Error creating combined file: {e}")

        logger.info(f"Extraction complete! Files saved to: {output_dir}")
        return output_dir

    def sync_extract_sitemap(
        self,
        sitemap_url: str,
        max_pages: Optional[int] = None
    ) -> Dict[str, str]:
        """Synchronous wrapper for extract_from_sitemap"""
        return asyncio.run(self.extract_from_sitemap(sitemap_url, max_pages))

    def sync_extract_domain(
        self,
        domain_url: str,
        max_pages: int = 50,
        deep_crawl: bool = True
    ) -> Dict[str, str]:
        """Synchronous wrapper for extract_from_domain"""
        return asyncio.run(self.extract_from_domain(domain_url, max_pages, deep_crawl))
