"""
Search Scraper Tab - AI-Powered Web Research
"""

import streamlit as st
import json
import datetime
import os
from pathlib import Path
from constants import MIN_NUM_SOURCES, MAX_NUM_SOURCES, DEFAULT_NUM_SOURCES


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

    col1, col2 = st.columns([3, 1])
    with col1:
        scraper_prompt = st.text_area(
            "Research Question or Query",
            placeholder="What are the latest developments in renewable energy technology?",
            height=100
        )
    with col2:
        num_sources = st.slider("Number of sources", MIN_NUM_SOURCES, MAX_NUM_SOURCES, DEFAULT_NUM_SOURCES)
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

    run_scraper = st.button("🔍 Search & Scrape", type="primary", width='stretch')

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
                    concurrency=int(settings.get("concurrency", 8))
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
