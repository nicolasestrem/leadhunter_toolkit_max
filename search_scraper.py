"""
SearchScraper: AI-powered web search and information extraction
"""
import asyncio
from typing import Optional, Dict, List, Any, TYPE_CHECKING, Iterable, Mapping
from markdownify import markdownify as md
from search import ddg_sites
from google_search import google_sites
from fetch import fetch_many, text_content
from llm_client import LLMClient
from constants import MIN_NUM_SOURCES, MAX_NUM_SOURCES, DEFAULT_NUM_SOURCES

if TYPE_CHECKING:
    from indexing.site_indexer import SiteIndexer


class SearchScraperResult:
    """Result from SearchScraper operation"""
    def __init__(self, mode: str, prompt: str):
        self.mode = mode
        self.prompt = prompt
        self.sources: List[Dict[str, str]] = []
        self.extracted_data: Optional[str] = None
        self.markdown_content: Optional[str] = None
        self.error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "prompt": self.prompt,
            "sources": self.sources,
            "extracted_data": self.extracted_data,
            "markdown_content": self.markdown_content,
            "error": self.error
        }


class SearchScraper:
    """
    AI-powered web search and content extraction tool

    Modes:
    - AI Extraction: Uses LLM to extract structured information (10 credits/page equivalent)
    - Markdown: Returns raw markdown content (2 credits/page equivalent)
    """

    def __init__(
        self,
        llm_base: str = "",
        llm_key: str = "",
        llm_model: str = "gpt-4o-mini",
        search_engine: str = "ddg",
        google_api_key: str = "",
        google_cx: str = ""
    ):
        self.llm_client = LLMClient(api_key=llm_key, base_url=llm_base, model=llm_model)
        self.search_engine = search_engine
        self.google_api_key = google_api_key
        self.google_cx = google_cx

    def _search_web(self, query: str, num_results: int) -> List[str]:
        """Search the web for relevant URLs"""
        if self.search_engine == "google" and self.google_api_key and self.google_cx:
            return google_sites(query, num_results, self.google_api_key, self.google_cx)
        else:
            return ddg_sites(query, num_results)

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to clean markdown"""
        if not html:
            return ""
        try:
            # Convert HTML to markdown with sensible options
            markdown = md(
                html,
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style', 'meta', 'link', 'noscript'],
                escape_asterisks=False,
                escape_underscores=False
            )
            # Clean up excessive whitespace
            lines = [line.strip() for line in markdown.split('\n') if line.strip()]
            return '\n\n'.join(lines)
        except Exception:
            # Fallback to text content if markdown conversion fails
            return text_content(html)

    async def search_and_scrape(
        self,
        prompt: str,
        num_results: int = DEFAULT_NUM_SOURCES,
        extraction_mode: bool = True,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
        concurrency: int = 6,
        indexer: Optional["SiteIndexer"] = None,
        dynamic_rendering: bool = False,
        dynamic_allowlist: Optional[Iterable[str]] = None,
        dynamic_selector_hints: Optional[Mapping[str, Iterable[str]]] = None,
    ) -> SearchScraperResult:
        """
        Search the web and extract information based on a prompt

        Args:
            prompt: The search query or research question
            num_results: Number of web pages to scrape (between MIN_NUM_SOURCES and MAX_NUM_SOURCES)
            extraction_mode: True for AI extraction, False for markdown mode
            schema: Optional JSON schema for structured extraction
            timeout: Request timeout in seconds
            concurrency: Number of concurrent requests
            indexer: Optional SiteIndexer instance to persist processed content
            dynamic_rendering: Enable Playwright-backed fetching for allowed domains
            dynamic_allowlist: Optional collection of domains eligible for dynamic rendering
            dynamic_selector_hints: Optional mapping of domain -> CSS selectors to await

        Returns:
            SearchScraperResult with extracted data or markdown content
        """
        result = SearchScraperResult(
            mode="ai_extraction" if extraction_mode else "markdown",
            prompt=prompt
        )

        # Validate inputs
        num_results = max(MIN_NUM_SOURCES, min(MAX_NUM_SOURCES, num_results))

        try:
            # Step 1: Search for relevant URLs
            urls = self._search_web(prompt, num_results)

            if not urls:
                result.error = "No search results found"
                return result

            # Step 2: Fetch all pages
            html_pages = await fetch_many(
                urls,
                timeout=timeout,
                concurrency=concurrency,
                use_cache=True,
                dynamic_rendering=dynamic_rendering,
                dynamic_allowlist=dynamic_allowlist,
                dynamic_selector_hints=dynamic_selector_hints,
            )

            # Step 3: Convert to markdown and build sources
            markdown_pages = []
            for url, html in html_pages.items():
                if not html:
                    continue

                markdown = self._html_to_markdown(html)
                if not markdown:
                    continue

                # Add source metadata
                result.sources.append({
                    "url": url,
                    "length": len(markdown),
                    "preview": markdown[:200] + "..." if len(markdown) > 200 else markdown
                })

                markdown_pages.append(f"## Source: {url}\n\n{markdown}")

                if indexer:
                    indexer.index_page(
                        url,
                        markdown,
                        metadata={
                            "source": "search_scraper",
                            "prompt": prompt,
                            "mode": "ai_extraction" if extraction_mode else "markdown",
                        },
                    )

            if not markdown_pages:
                result.error = "No content could be extracted from search results"
                return result

            # Step 4: Process based on mode
            if extraction_mode:
                # AI Extraction Mode: Use LLM to synthesize information
                result.extracted_data = await self._ai_extract(prompt, markdown_pages, schema)
            else:
                # Markdown Mode: Return concatenated markdown
                separator = "\n\n" + "=" * 80 + "\n\n"
                result.markdown_content = separator.join(markdown_pages)

        except Exception as e:
            result.error = f"Error during search and scrape: {str(e)}"

        return result

    async def _ai_extract(
        self,
        prompt: str,
        markdown_pages: List[str],
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """Use LLM to extract structured information from markdown content"""

        # Combine all markdown content (with length limit for LLM context)
        combined = "\n\n".join(markdown_pages)
        max_context = 15000  # Approx 4000 tokens
        if len(combined) > max_context:
            combined = combined[:max_context] + "\n\n[Content truncated due to length...]"

        # Build extraction prompt
        if schema:
            system_prompt = f"""You are a research assistant. Extract information from the provided web content to answer the user's question.

User Question: {prompt}

Desired Output Schema:
{schema}

Please extract the relevant information and structure it according to the schema above.
"""
        else:
            system_prompt = f"""You are a research assistant. Analyze the provided web content and answer the user's question comprehensively.

User Question: {prompt}

Instructions:
1. Synthesize information from multiple sources
2. Provide specific facts, figures, and examples
3. Cite sources when possible (mention URLs)
4. Be concise but thorough
5. If sources conflict, mention different perspectives
"""

        full_prompt = f"{system_prompt}\n\nWeb Content:\n\n{combined}\n\nYour comprehensive answer:"

        # Call LLM (synchronous call wrapped in async)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.llm_client.summarize_leads,
            [],  # No leads, using custom instruction
            full_prompt
        )

        return result

    def sync_search_and_scrape(
        self,
        prompt: str,
        num_results: int = DEFAULT_NUM_SOURCES,
        extraction_mode: bool = True,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 15,
        concurrency: int = 6,
        indexer: Optional["SiteIndexer"] = None
    ) -> SearchScraperResult:
        """Synchronous wrapper for search_and_scrape"""
        return asyncio.run(
            self.search_and_scrape(
                prompt,
                num_results,
                extraction_mode,
                schema,
                timeout,
                concurrency,
                indexer=indexer,
            )
        )
