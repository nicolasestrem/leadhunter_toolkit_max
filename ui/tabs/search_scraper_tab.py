"""
Search Scraper Tab - AI-Powered Web Research
"""

import streamlit as st
import json
import datetime
import os
from pathlib import Path
from constants import MIN_NUM_SOURCES, MAX_NUM_SOURCES, DEFAULT_NUM_SOURCES
from indexing import SiteIndexer


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
                    path = os.path.join(out_dir, filename)
                    with open(path, "w", encoding="utf-8") as f:
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
                    path = os.path.join(out_dir, filename)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"# Query: {result.prompt}\n\n")
                        f.write(f"## Sources\n\n")
                        for source in result.sources:
                            f.write(f"- [{source['url']}]({source['url']})\n")
                        f.write(f"\n\n## Content\n\n{result.markdown_content}")
                    st.success(f"Saved to {path}")

    st.divider()
    st.subheader("Semantic Search of Indexed Pages")
    st.caption("Query previously processed content with optional filters.")

    with st.form("semantic_index_search"):
        query_text = st.text_input("Semantic query", key="index_query")
        col_filters = st.columns(3)
        with col_filters[0]:
            domain_filter = st.text_input("Domain filter", placeholder="example.com", key="index_domain")
        with col_filters[1]:
            start_date = st.text_input("Start date (YYYY-MM-DD)", key="index_start")
        with col_filters[2]:
            end_date = st.text_input("End date (YYYY-MM-DD)", key="index_end")
        top_k = st.slider("Max results", 1, 10, 5)
        submitted = st.form_submit_button("Search Index")

    if submitted:
        if not query_text.strip():
            st.warning("Please provide a query to search the index.")
        else:
            results = indexer.query(
                query_text,
                top_k=top_k,
                domain=domain_filter or None,
                start_date=start_date or None,
                end_date=end_date or None,
            )
            if not results:
                st.info("No indexed chunks matched the query and filters.")
            else:
                for item in results:
                    st.markdown(f"**[{item.url}]({item.url})** — Score: {item.score:.3f}")
                    st.caption(
                        f"Timestamp: {item.timestamp or 'unknown'} | Domain: {item.domain or 'n/a'} | Chunk #{item.chunk_index}"
                    )
                    preview = item.text.strip()
                    if len(preview) > 500:
                        preview = preview[:500] + "…"
                    st.write(preview)
                    if item.metadata:
                        meta_str = ", ".join(f"{k}: {v}" for k, v in item.metadata.items())
                        st.caption(f"Metadata: {meta_str}")
                    st.divider()
