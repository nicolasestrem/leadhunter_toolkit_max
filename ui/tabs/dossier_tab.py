"""
Dossier Tab - Client dossier builder with RAG
"""

import streamlit as st
import asyncio
import datetime
from pathlib import Path
from config.loader import ConfigLoader
from llm.adapter import LLMAdapter
from dossier.build import build_dossier
from fetch import fetch_many, text_content
from constants import MIN_DOSSIER_NUM_PAGES, MAX_DOSSIER_NUM_PAGES, DEFAULT_DOSSIER_NUM_PAGES
from constants import MIN_DOSSIER_CRAWL_PAGES, MAX_DOSSIER_CRAWL_PAGES, DEFAULT_DOSSIER_CRAWL_PAGES


def get_llm_adapter():
    """Helper function to create LLM adapter"""
    config_loader = ConfigLoader()
    config = config_loader.get_merged_config()
    return LLMAdapter.from_config(config)


def render_dossier_tab(settings: dict, out_dir: str):
    """
    Render the Dossier tab

    Args:
        settings: Application settings dict
        out_dir: Output directory path
    """
    st.subheader("Client Dossier Builder")
    st.caption("Generate comprehensive RAG-based client dossiers with cited sources and quick wins")

    # Check if we have a selected lead
    if st.session_state.get("selected_lead"):
        lead = st.session_state["selected_lead"]
        st.info(f"**Building dossier for:** {lead.get('name', 'Unknown')} ({lead.get('domain', 'N/A')})")

        # Input for pages to analyze
        st.markdown("### Pages to Analyze")
        st.caption("Provide URLs or paste page content to include in the dossier")

        page_input_mode = st.radio("Input Mode", ["URLs (will crawl)", "Paste Content"])

        pages_data = []

        if page_input_mode == "URLs (will crawl)":
            urls_input = st.text_area(
                "URLs (one per line)",
                placeholder=f"{lead.get('website', 'https://example.com')}\n{lead.get('website', 'https://example.com')}/about",
                height=150
            )

            max_pages_crawl = st.slider("Max pages to crawl", MIN_DOSSIER_CRAWL_PAGES, MAX_DOSSIER_CRAWL_PAGES, DEFAULT_DOSSIER_CRAWL_PAGES)

            if st.button("🕷️ Crawl Pages"):
                if urls_input.strip():
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    try:
                        urls = [u.strip() for u in urls_input.splitlines() if u.strip().startswith("http")]
                        status_text.text(f"🕷️ Crawling {len(urls)} URLs...")
                        progress_bar.progress(0.1)

                        # Fetch pages
                        with st.spinner("Fetching pages in parallel..."):
                            pages_dict = asyncio.run(fetch_many(
                                urls,
                                timeout=int(settings.get("fetch_timeout", 15)),
                                concurrency=int(settings.get("concurrency", 8))
                            ))

                        status_text.text(f"📄 Processing {len(pages_dict)} pages...")
                        progress_bar.progress(0.7)

                        # Convert to pages data format
                        for url, html in pages_dict.items():
                            if html:
                                content = text_content(html)
                                pages_data.append({"url": url, "content": content})

                        st.session_state["dossier_pages"] = pages_data

                        progress_bar.progress(1.0)
                        status_text.text(f"✓ Crawled {len(pages_data)} pages")
                        total_chars = sum(len(p.get('content', '')) for p in pages_data)
                        st.success(f"✅ Fetched {len(pages_data)} pages with {total_chars} total characters")
                        st.toast(f"Crawled {len(pages_data)} pages", icon="✅")

                    except Exception as e:
                        st.error(f"Crawl failed: {str(e)}")
                        status_text.text("❌ Crawl failed")
                else:
                    st.warning("Please enter at least one URL")

        else:  # Paste Content
            num_pages = st.number_input("Number of pages", min_value=MIN_DOSSIER_NUM_PAGES, max_value=MAX_DOSSIER_NUM_PAGES, value=DEFAULT_DOSSIER_NUM_PAGES)

            for i in range(num_pages):
                with st.expander(f"Page {i+1}", expanded=(i==0)):
                    url = st.text_input(f"URL {i+1}", key=f"dossier_url_{i}",
                                       value=lead.get('website', '') if i == 0 else '')
                    content = st.text_area(f"Content {i+1}", key=f"dossier_content_{i}",
                                          height=100, placeholder="Paste page content here...")

                    if url and content.strip():
                        # Check if already added
                        existing = next((p for p in pages_data if p['url'] == url), None)
                        if existing:
                            existing['content'] = content
                        else:
                            pages_data.append({"url": url, "content": content})

            if st.button("Save Pages"):
                st.session_state["dossier_pages"] = pages_data
                st.success(f"Saved {len(pages_data)} pages")

        # Show collected pages
        if st.session_state.get("dossier_pages"):
            st.divider()
            st.markdown(f"### Collected Pages ({len(st.session_state['dossier_pages'])})")

            for i, page in enumerate(st.session_state["dossier_pages"], 1):
                st.caption(f"{i}. {page['url']} ({len(page.get('content', ''))} chars)")

            # Generate dossier
            if st.button("📋 Generate Dossier", type="primary"):
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                try:
                    adapter = get_llm_adapter()

                    # Multi-phase progress tracking
                    status_text.text("🚀 Initializing dossier builder...")
                    progress_bar.progress(0.05)

                    status_text.text("📊 Analyzing company overview...")
                    progress_bar.progress(0.15)

                    # Prepare output directory
                    project = settings.get("project", "default")
                    out_path = Path(out_dir) / project / "dossiers"

                    status_text.text("🔍 Extracting services and products...")
                    progress_bar.progress(0.3)

                    status_text.text("🌐 Analyzing digital presence...")
                    progress_bar.progress(0.45)

                    status_text.text("📡 Detecting signals (positive, growth, pain)...")
                    progress_bar.progress(0.6)

                    status_text.text("⚠️ Identifying issues...")
                    progress_bar.progress(0.75)

                    status_text.text("⚡ Generating 48-hour quick wins...")
                    progress_bar.progress(0.85)

                    # Build dossier
                    with st.spinner("🤖 LLM processing all sections..."):
                        dossier = build_dossier(
                            lead_data=lead,
                            pages=st.session_state["dossier_pages"],
                            llm_adapter=adapter,
                            output_dir=out_path
                        )

                    st.session_state["dossier_result"] = dossier

                    progress_bar.progress(1.0)
                    status_text.text("✓ Dossier complete!")
                    st.success(f"✅ Generated comprehensive dossier with {len(dossier.sources)} sources, {len(dossier.quick_wins)} quick wins")
                    st.toast("Dossier ready!", icon="📋")

                except Exception as e:
                    st.error(f"Dossier generation failed: {str(e)}")
                    status_text.text("❌ Generation failed")

    # Display dossier
    if st.session_state.get("dossier_result"):
        dossier = st.session_state["dossier_result"]

        st.divider()
        st.subheader(f"📊 Dossier: {dossier.company_name}")

        # Overview
        with st.expander("🏢 Company Overview", expanded=True):
            st.markdown(dossier.company_overview)
            st.caption(f"Website: {dossier.website}")
            st.caption(f"Pages analyzed: {dossier.pages_analyzed}")

        # Services/Products
        with st.expander(f"🛍️ Services & Products ({len(dossier.services_products)} items)", expanded=True):
            for item in dossier.services_products:
                st.markdown(f"- {item}")

        # Digital Presence
        with st.expander("🌐 Digital Presence", expanded=True):
            dp = dossier.digital_presence
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Website Quality:**")
                st.write(dp.website_quality or "Not analyzed")
            with col2:
                st.markdown("**Social Activity:**")
                st.write(dp.social_activity or "Not analyzed")

            if hasattr(dp, 'online_reputation') and dp.online_reputation:
                st.markdown("**Online Reputation:**")
                st.write(dp.online_reputation)

        # Signals
        with st.expander("📡 Signals", expanded=True):
            signals = dossier.signals
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**✅ Positive Signals:**")
                for sig in signals.positive:
                    st.caption(f"- {sig}")

            with col2:
                st.markdown("**📈 Growth Signals:**")
                for sig in signals.growth:
                    st.caption(f"- {sig}")

            with col3:
                st.markdown("**⚠️ Pain Signals:**")
                for sig in signals.pain:
                    st.caption(f"- {sig}")

        # Issues
        if dossier.issues:
            with st.expander(f"🔍 Issues Detected ({len(dossier.issues)})", expanded=True):
                for issue in dossier.issues:
                    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity.lower(), "⚪")
                    st.markdown(f"{severity_icon} **{issue.category}** - {issue.description}")
                    st.caption(f"Source: {issue.source}")
                    st.divider()

        # Quick Wins
        if dossier.quick_wins:
            with st.expander(f"⚡ 48-Hour Quick Wins ({len(dossier.quick_wins)})", expanded=True):
                for i, qw in enumerate(dossier.quick_wins, 1):
                    st.markdown(f"### {i}. {qw.title}")
                    st.markdown(f"**Action:** {qw.action}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Impact", qw.impact)
                    with col2:
                        st.metric("Effort", qw.effort)
                    with col3:
                        st.metric("Priority", f"{qw.priority:.1f}/10")

                    st.divider()

        # Sources
        with st.expander(f"📚 Sources ({len(dossier.sources)})", expanded=False):
            for i, source in enumerate(dossier.sources, 1):
                st.markdown(f"{i}. [{source}]({source})")

        # Export
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Export as Markdown"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)

                # Dossier should already be saved by build_dossier
                st.success(f"Dossier saved in {out_path}")

        with col2:
            if st.button("📦 Export as JSON"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)

                # Dossier should already be saved by build_dossier
                st.success(f"Dossier saved in {out_path}")
    else:
        st.info("👈 Select a lead from the Leads tab and collect pages to analyze.")
