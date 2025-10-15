"""
Search Scraper Tab - AI-Powered Web Research
"""

import datetime
import json
import streamlit as st
from collections.abc import Iterable
from pathlib import Path
from typing import Optional
from constants import MIN_NUM_SOURCES, MAX_NUM_SOURCES, DEFAULT_NUM_SOURCES
from crawl import CrawlConfig
from indexing.site_indexer import SiteIndexer
from scraping.pipeline import (
    PipelineResult,
    run_search_pipeline_sync,
    run_site_pipeline_sync,
)
from google_search import google_sites
from search import ddg_sites


def get_search_scraper():
    """Lazy load SearchScraper module"""
    from search_scraper import SearchScraper
    return SearchScraper


def render_search_scraper_tab(settings: dict, out_dir: str):
    """
    Render the Search Scraper tab

    Args:
        settings: Application settings dict
        out_dir: Output directory path
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    st.subheader("AI-Powered Web Research")
    st.caption("Search the web and extract insights using AI, or get raw markdown content from multiple sources")

    index_path = Path(out_dir) / "site_index"

    @st.cache_resource(show_spinner=False)
    def _get_cached_indexer(path: str) -> SiteIndexer:
        return SiteIndexer(path)

    indexer = _get_cached_indexer(str(index_path))
    st.caption(f"Indexed chunks available: {len(indexer.metadata)}")

    col1, col2 = st.columns([3, 1])
    with col1:
        scraper_prompt = st.text_area(
            "Research Question or Query",
            placeholder="What are the latest developments in renewable energy technology?",
            height=100
        )
    with col2:
        num_sources = st.slider(
            "Number of sources",
            MIN_NUM_SOURCES,
            MAX_NUM_SOURCES,
            DEFAULT_NUM_SOURCES,
            step=1,
            help=f"Choose how many search results to fetch ({MIN_NUM_SOURCES}-{MAX_NUM_SOURCES}). Use the keyboard or type a value for quicker adjustments. Larger batches may take longer."
        )
        extraction_mode = st.selectbox(
            "Mode",
            ["AI Extraction", "Markdown"],
            help="AI Extraction: Get structured insights (uses LLM). Markdown: Get raw content (faster, no AI)"
        )

    # Optional schema for structured extraction
    use_schema = st.checkbox("Use custom extraction schema (advanced)")
    schema_json = None
    if use_schema:
        schema_input = st.text_area(
            "JSON Schema",
            placeholder='{"key_findings": ["string"], "sources": ["string"]}',
            height=100
        )
        if schema_input.strip():
            try:
                schema_json = json.loads(schema_input)
            except json.JSONDecodeError:
                st.warning("Invalid JSON schema. Will use default extraction.")

    dynamic_rendering_default = bool(settings.get("dynamic_rendering", False))
    dynamic_allowlist: Optional[set[str]] = None
    dynamic_selector_hints: Optional[dict[str, list[str]]] = None

    with st.expander("Advanced fetching options", expanded=dynamic_rendering_default):
        dynamic_rendering = st.toggle(
            "Enable dynamic rendering (Playwright)",
            value=dynamic_rendering_default,
            help="Fetch pages with a headless browser for sites that require JavaScript rendering.",
        )

        allowlist_default = settings.get("dynamic_allowlist", "")
        if isinstance(allowlist_default, (list, tuple, set)):
            allowlist_default = ", ".join(str(domain) for domain in allowlist_default)
        allowlist_input = st.text_input(
            "Dynamic rendering allowlist",
            value=str(allowlist_default) if allowlist_default else "",
            help="Comma or newline separated domains allowed for Playwright rendering.",
            placeholder="example.com, example.org",
        )

        hints_default = settings.get("dynamic_selector_hints", "")
        if isinstance(hints_default, dict):
            try:
                hints_default = json.dumps(hints_default, indent=2)
            except (TypeError, ValueError):
                hints_default = ""
        hints_input = st.text_area(
            "Selector hints (JSON)",
            value=str(hints_default) if hints_default else "",
            help="Optional JSON mapping of domain to CSS selectors to await when using Playwright.",
            placeholder='{"example.com": [".content", "#main"]}',
        )

        if dynamic_rendering:
            cleaned_allowlist: set[str] = set()
            if allowlist_input.strip():
                for chunk in allowlist_input.replace("\n", ",").split(","):
                    domain = chunk.strip().lower()
                    if domain:
                        cleaned_allowlist.add(domain)
            dynamic_allowlist = cleaned_allowlist or None

            if hints_input.strip():
                try:
                    parsed_hints = json.loads(hints_input)
                    if isinstance(parsed_hints, dict):
                        cleaned_hints: dict[str, list[str]] = {}
                        for domain, selectors in parsed_hints.items():
                            domain_label = str(domain).strip()
                            if not domain_label:
                                st.warning(
                                    "Selector hints entries require a non-empty domain key. Ignoring entry.",
                                    icon="⚠️",
                                )
                                continue

                            if isinstance(selectors, str):
                                selector_iterable = [selectors]
                            elif isinstance(selectors, Iterable) and not isinstance(selectors, (dict, str)):
                                selector_iterable = selectors
                            else:
                                st.warning(
                                    f"Selector hints for {domain_label!r} must be a string or list of strings. Ignoring entry.",
                                    icon="⚠️",
                                )
                                continue

                            cleaned_selectors: list[str] = []
                            for selector in selector_iterable:
                                selector_text = str(selector).strip()
                                if selector_text:
                                    cleaned_selectors.append(selector_text)

                            if cleaned_selectors:
                                unique_selectors = list(dict.fromkeys(cleaned_selectors))
                                cleaned_hints[domain_label.lower()] = unique_selectors
                            else:
                                st.warning(
                                    f"Selector hints for {domain_label!r} did not include any selectors. Ignoring entry.",
                                    icon="⚠️",
                                )

                        dynamic_selector_hints = cleaned_hints or None
                    else:
                        st.warning("Selector hints must be a JSON object mapping domains to selectors.", icon="⚠️")
                except json.JSONDecodeError:
                    st.warning("Invalid JSON for selector hints. Ignoring value.", icon="⚠️")
            else:
                dynamic_selector_hints = None
        else:
            dynamic_allowlist = None
            dynamic_selector_hints = None

    def build_dynamic_fetch_kwargs() -> dict[str, object]:
        if not dynamic_rendering:
            return {}

        kwargs: dict[str, object] = {"dynamic_rendering": True}
        if dynamic_allowlist is not None:
            kwargs["dynamic_allowlist"] = dynamic_allowlist
        if dynamic_selector_hints:
            kwargs["dynamic_selector_hints"] = dynamic_selector_hints
        return kwargs

    dynamic_fetch_kwargs = build_dynamic_fetch_kwargs()

    run_scraper = st.button("🔍 Search & Scrape", type="primary", use_container_width=True)

    if run_scraper and scraper_prompt.strip():
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        try:
            # Create SearchScraper instance with user's configured model
            scraper = get_search_scraper()(
                llm_base=settings.get("llm_base", ""),
                llm_key=settings.get("llm_key", ""),
                llm_model=settings.get("llm_model", "gpt-4o-mini"),  # Respect user's model choice
                search_engine=settings.get("search_engine", "ddg"),
                google_api_key=settings.get("google_cse_key", ""),
                google_cx=settings.get("google_cse_cx", "")
            )

            status_text.text("🔍 Searching the web...")
            progress_bar.progress(0.1)

            status_text.text(f"🌐 Fetching {num_sources} sources...")
            progress_bar.progress(0.3)

            status_text.text("📄 Converting HTML to markdown...")
            progress_bar.progress(0.6)

            if extraction_mode == "AI Extraction":
                status_text.text("🤖 Running LLM extraction and synthesis...")
                progress_bar.progress(0.8)

            # Run search and scrape
            with st.spinner(f"Processing {num_sources} sources..."):
                result = scraper.sync_search_and_scrape(
                    prompt=scraper_prompt,
                    num_results=num_sources,
                    extraction_mode=(extraction_mode == "AI Extraction"),
                    schema=schema_json,
                    timeout=int(settings.get("fetch_timeout", 15)),
                    concurrency=int(settings.get("concurrency", 8)),
                    indexer=indexer,
                    **dynamic_fetch_kwargs,
                )

            st.session_state["search_scraper_result"] = result

            progress_bar.progress(1.0)
            status_text.text("✓ Search scraping complete!")
            st.success(f"✅ Processed {len(result.sources)} sources in {extraction_mode} mode")
            st.toast("Research complete!", icon="🔍")

        except Exception as e:
            st.error(f"Error during search scraping: {str(e)}")
            status_text.text("❌ Scraping failed")

    # Display results
    if st.session_state.get("search_scraper_result"):
        result = st.session_state["search_scraper_result"]

        if result.error:
            st.error(result.error)
        else:
            st.success(f"Processed {len(result.sources)} sources")

            # Show sources
            with st.expander(f"📚 Sources ({len(result.sources)})", expanded=False):
                for i, source in enumerate(result.sources, 1):
                    st.markdown(f"**{i}. [{source['url']}]({source['url']})**")
                    st.caption(f"Length: {source['length']} chars | Preview: {source['preview'][:150]}...")
                    st.divider()

            # Show results based on mode
            if result.mode == "ai_extraction" and result.extracted_data:
                st.subheader("🤖 AI Extracted Insights")
                st.markdown(result.extracted_data)

                # Export option
                if st.button("💾 Export as Text"):
                    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                    filename = f"search_scraper_ai_{timestamp}.txt"
                    path = out_path / filename
                    with path.open("w", encoding="utf-8") as f:
                        f.write(f"Query: {result.prompt}\n\n")
                        f.write(f"Sources:\n")
                        for source in result.sources:
                            f.write(f"- {source['url']}\n")
                        f.write(f"\n\nExtracted Insights:\n\n{result.extracted_data}")
                    st.success(f"Saved to {path}")

            elif result.mode == "markdown" and result.markdown_content:
                st.subheader("📄 Markdown Content")
                st.text_area("Full Content", result.markdown_content, height=400)

                # Export option
                if st.button("💾 Export as Markdown"):
                    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                    filename = f"search_scraper_md_{timestamp}.md"
                    path = out_path / filename
                    with path.open("w", encoding="utf-8") as f:
                        f.write(f"# Query: {result.prompt}\n\n")
                        f.write(f"## Sources\n\n")
                        for source in result.sources:
                            f.write(f"- [{source['url']}]({source['url']})\n")
                        f.write(f"\n\n## Content\n\n{result.markdown_content}")
                    st.success(f"Saved to {path}")

    # ------------------------------------------------------------------
    # Contact discovery pipeline
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("Contact Discovery Pipeline")
    st.caption("Crawl a site or search the web, then consolidate emails, phones, and social links with source attribution.")

    pipeline_mode = st.radio(
        "Source", ["Website Crawl", "Search Query"], horizontal=True, key="pipeline_mode"
    )

    col_extract1, col_extract2, col_extract3, col_extract4 = st.columns(4)
    with col_extract1:
        extract_emails = st.checkbox("Extract Emails", value=True, key="pipeline_emails")
    with col_extract2:
        extract_phones = st.checkbox("Extract Phones", value=True, key="pipeline_phones")
    with col_extract3:
        extract_social = st.checkbox("Extract Social", value=True, key="pipeline_social")
    with col_extract4:
        extract_structured = st.checkbox(
            "Parse Structured Data",
            value=True,
            key="pipeline_structured",
            help="Parse schema.org JSON-LD and microdata for contact details",
        )

    extraction_settings = {
        "extract_emails": extract_emails,
        "extract_phones": extract_phones,
        "extract_social": extract_social,
        "extract_structured": extract_structured,
    }

    pipeline_result: Optional[PipelineResult] = st.session_state.get("pipeline_result")
    fetch_timeout = int(settings.get("fetch_timeout", 15))
    concurrency = int(settings.get("concurrency", 6))

    if pipeline_mode == "Website Crawl":
        crawl_url = st.text_input("Website URL", placeholder="https://example.com", key="pipeline_site_url")
        crawl_col1, crawl_col2, crawl_col3 = st.columns(3)
        with crawl_col1:
            max_pages = st.slider("Max Pages", min_value=1, max_value=20, value=5, key="pipeline_max_pages")
        with crawl_col2:
            deep_contact = st.checkbox("Prioritize Contact Pages", value=True, key="pipeline_deep_contact")
        with crawl_col3:
            crawl_timeout = st.number_input(
                "Timeout (s)", min_value=5, max_value=60, value=fetch_timeout, key="pipeline_crawl_timeout"
            )

        run_pipeline = st.button("🚀 Run Contact Pipeline", key="pipeline_run_site", use_container_width=True)

        if run_pipeline:
            if not crawl_url.strip():
                st.warning("Please provide a website URL to crawl.")
            else:
                try:
                    with st.spinner("Crawling site and extracting contacts..."):
                        crawl_params = {
                            "timeout": int(crawl_timeout),
                            "concurrency": concurrency,
                            "max_pages": int(max_pages),
                            "deep_contact": bool(deep_contact),
                        }
                        if dynamic_rendering:
                            crawl_params["config"] = CrawlConfig(
                                dynamic_rendering=True,
                                dynamic_allowed_domains=dynamic_allowlist,
                            )

                        pipeline_result = run_site_pipeline_sync(
                            crawl_url.strip(),
                            crawl_kwargs=crawl_params,
                            extraction_settings=extraction_settings,
                        )
                    st.session_state["pipeline_result"] = pipeline_result
                except Exception as exc:
                    st.error(f"Error running pipeline: {exc}")

    else:
        search_query = st.text_input("Search Query", placeholder="best marketing agencies in Paris", key="pipeline_search_query")
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            max_results = st.slider("Results", min_value=3, max_value=15, value=5, key="pipeline_max_results")
        with search_col2:
            fetch_timeout_input = st.number_input(
                "Timeout (s)", min_value=5, max_value=60, value=fetch_timeout, key="pipeline_search_timeout"
            )

        run_pipeline = st.button("🔎 Run Contact Pipeline", key="pipeline_run_search", use_container_width=True)

        if run_pipeline:
            if not search_query.strip():
                st.warning("Please provide a search query.")
            else:
                try:
                    search_engine = (settings.get("search_engine") or "ddg").lower()
                    google_kwargs = None
                    if search_engine == "google":
                        google_kwargs = {
                            "api_key": settings.get("google_cse_key", ""),
                            "cx": settings.get("google_cse_cx", ""),
                        }
                        search_callable = google_sites
                    else:
                        search_callable = ddg_sites

                    with st.spinner("Fetching search results and extracting contacts..."):
                        fetch_kwargs = {
                            "timeout": int(fetch_timeout_input),
                            "concurrency": concurrency,
                            "use_cache": True,
                        }
                        fetch_kwargs.update(dynamic_fetch_kwargs)

                        pipeline_result = run_search_pipeline_sync(
                            search_query.strip(),
                            search_func=search_callable,
                            max_results=int(max_results),
                            fetch_kwargs=fetch_kwargs,
                            extraction_settings=extraction_settings,
                            google_kwargs=google_kwargs,
                        )
                    st.session_state["pipeline_result"] = pipeline_result
                except Exception as exc:
                    st.error(f"Error running pipeline: {exc}")

    if pipeline_result:
        st.success(
            f"Pipeline processed {pipeline_result.page_count} pages with "
            f"{len(pipeline_result.contacts.get('emails', []))} emails, "
            f"{len(pipeline_result.contacts.get('phones', []))} phones, and "
            f"{len(pipeline_result.contacts.get('social', []))} social profiles."
        )

        col_metrics = st.columns(3)
        col_metrics[0].metric("Pages", pipeline_result.page_count)
        col_metrics[1].metric("Emails", len(pipeline_result.contacts.get("emails", [])))
        col_metrics[2].metric("Phones", len(pipeline_result.contacts.get("phones", [])))

        if pipeline_result.contacts.get("emails"):
            with st.expander("Email Addresses", expanded=False):
                for entry in pipeline_result.contacts["emails"]:
                    st.markdown(
                        f"- **{entry['email']}**  \n  Sources: {', '.join(entry['sources'])}"
                    )

        if pipeline_result.contacts.get("phones"):
            with st.expander("Phone Numbers", expanded=False):
                for entry in pipeline_result.contacts["phones"]:
                    st.markdown(
                        f"- **{entry['phone']}**  \n  Sources: {', '.join(entry['sources'])}"
                    )

        if pipeline_result.contacts.get("social"):
            with st.expander("Social Profiles", expanded=False):
                for entry in pipeline_result.contacts["social"]:
                    st.markdown(
                        f"- **{entry['network'].title()}**: {entry['url']}  \n  Sources: {', '.join(entry['sources'])}"
                    )

        with st.expander(f"Processed Pages ({pipeline_result.page_count})", expanded=False):
            for page in pipeline_result.pages:
                st.markdown(f"**{page.title or page.url}**")
                st.caption(page.url)
                if page.meta_description:
                    st.caption(page.meta_description)
                page_contacts = []
                if page.extraction.get("emails"):
                    page_contacts.append(f"Emails: {', '.join(page.extraction['emails'])}")
                if page.extraction.get("phones"):
                    page_contacts.append(f"Phones: {', '.join(page.extraction['phones'])}")
                if page.extraction.get("social"):
                    socials = ", ".join(
                        f"{network}: {link}" for network, link in page.extraction["social"].items()
                    )
                    page_contacts.append(f"Social: {socials}")
                if page_contacts:
                    st.caption(" | ".join(page_contacts))
                if page.markdown:
                    st.text_area(
                        "Markdown Preview",
                        page.markdown[:1000] + ("..." if len(page.markdown) > 1000 else ""),
                        height=150,
                        key=f"pipeline_md_{hash(page.url)}",
                    )
                st.divider()

        json_payload = json.dumps(pipeline_result.to_dict(), ensure_ascii=False, indent=2)
        st.download_button(
            "⬇️ Download JSON",
            data=json_payload,
            file_name="pipeline_results.json",
            mime="application/json",
        )

        if st.button("💾 Save results to disk", key="pipeline_save_disk"):
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"pipeline_{pipeline_result.mode}_{timestamp}.json"
            path = out_path / filename
            with path.open("w", encoding="utf-8") as f:
                f.write(json_payload)
            st.success(f"Saved pipeline results to {path}")
