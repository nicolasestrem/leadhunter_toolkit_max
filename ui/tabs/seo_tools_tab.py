"""
SEO Tools Tab - Content Audit, SERP Tracker, Site Extractor
"""

import streamlit as st
import datetime
import os
import httpx
import pandas as pd
from urllib.parse import urlparse
from llm_client import LLMClient
from constants import (MIN_SERP_RESULTS, MAX_SERP_RESULTS, DEFAULT_SERP_RESULTS,
                       MIN_SITEMAP_PAGES, MAX_SITEMAP_PAGES, DEFAULT_SITEMAP_PAGES,
                       MIN_SITE_CRAWL_PAGES, MAX_SITE_CRAWL_PAGES, DEFAULT_SITE_CRAWL_PAGES)


def get_seo_auditor():
    """Lazy load the SEOAuditor module.

    This function dynamically imports the SEOAuditor class to avoid circular
    dependencies and to improve startup time.

    Returns:
        The SEOAuditor class.
    """
    from seo_audit import SEOAuditor
    return SEOAuditor


def get_serp_tracker():
    """Lazy load the SERPTracker module.

    This function dynamically imports the SERPTracker class.

    Returns:
        The SERPTracker class.
    """
    from serp_tracker import SERPTracker
    return SERPTracker


def get_site_extractor():
    """Lazy load the SiteExtractor module.

    This function dynamically imports the SiteExtractor class.

    Returns:
        The SiteExtractor class.
    """
    from site_extractor import SiteExtractor
    return SiteExtractor


def render_seo_tools_tab(settings: dict, out_dir: str):
    """Render the SEO Tools tab in the Streamlit UI.

    This function provides the user interface for a suite of SEO tools, including a
    content auditor, a SERP tracker, and a site extractor.

    Args:
        settings (dict): The current application settings.
        out_dir (str): The path to the output directory.
    """
    st.subheader("SEO Tools")
    st.caption("Comprehensive SEO analysis, SERP tracking, and site extraction")

    seo_tab1, seo_tab2, seo_tab3 = st.tabs(["Content Audit", "SERP Tracker", "Site Extractor"])

    # --- Content Audit Sub-tab ---
    with seo_tab1:
        st.markdown("### SEO Content Audit")
        st.caption("Analyze a web page for SEO quality with optional LLM scoring")

        audit_url = st.text_input("URL to audit", placeholder="https://example.com")
        use_llm_scoring = st.checkbox("Use LLM content scoring", value=True)

        if st.button("Run SEO Audit", type="primary"):
            if audit_url:
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                try:
                    # Fetch page
                    status_text.text("🌐 Fetching page...")
                    progress_bar.progress(0.15)

                    resp = httpx.get(audit_url, timeout=15, follow_redirects=True, headers={"User-Agent": "LeadHunter/1.0"})
                    resp.raise_for_status()
                    html = resp.text

                    # Create auditor
                    status_text.text("🔧 Initializing SEO auditor...")
                    progress_bar.progress(0.3)

                    llm_client = None
                    if use_llm_scoring and settings.get("llm_base"):
                        llm_client = LLMClient(
                            api_key=settings.get("llm_key", ""),
                            base_url=settings.get("llm_base", ""),
                            model=settings.get("llm_model", "gpt-4o-mini"),  # Respect user's model choice
                            temperature=float(settings.get("llm_temperature", 0.4)),
                            top_p=float(settings.get("llm_top_p", 0.9)),
                            max_tokens=int(settings.get("llm_max_tokens", 2048)) or None
                        )

                    auditor = get_seo_auditor()(llm_client=llm_client)

                    # Run audit
                    status_text.text("📊 Analyzing meta tags, headings, images...")
                    progress_bar.progress(0.5)

                    status_text.text("🔗 Analyzing links and content structure...")
                    progress_bar.progress(0.7)

                    if use_llm_scoring:
                        status_text.text("🤖 Running LLM content quality analysis...")
                        progress_bar.progress(0.85)

                    result = auditor.audit_url(audit_url, html)

                    progress_bar.progress(1.0)
                    status_text.text("✓ SEO audit complete!")
                    st.toast(f"SEO Score: {result.seo_score}/100", icon="📊")

                    # Display results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("SEO Score", f"{result.seo_score:.0f}/100")
                    with col2:
                        st.metric("Word Count", result.word_count)
                    with col3:
                        st.metric("Total Issues", len(result.issues))

                    # Meta tags
                    with st.expander("📝 Meta Tags", expanded=True):
                        st.write(f"**Title:** {result.title}")
                        st.caption(f"Length: {result.title_length} chars (optimal: 50-60)")

                        st.write(f"**Meta Description:** {result.meta_description}")
                        st.caption(f"Length: {result.meta_description_length} chars (optimal: 150-160)")

                        if result.canonical_url:
                            st.write(f"**Canonical:** {result.canonical_url}")

                        if result.og_tags:
                            st.write("**Open Graph Tags:**")
                            for key, val in result.og_tags.items():
                                st.caption(f"- {key}: {val}")

                    # Headings
                    with st.expander(f"📑 Headings ({sum(result.heading_structure.values())} total)"):
                        st.write("**H1 Tags:**", result.h1_tags if result.h1_tags else "None")
                        st.write("**H2 Tags:**", result.h2_tags if result.h2_tags else "None")
                        st.write("**Structure:**", result.heading_structure)

                    # Images
                    with st.expander(f"🖼️ Images ({result.total_images} total, {result.image_alt_coverage:.1f}% with alt)"):
                        st.write(f"Images with alt text: {result.images_with_alt}")
                        st.write(f"Images missing alt text: {result.images_without_alt}")

                    # Links
                    with st.expander(f"🔗 Links ({result.total_links} total)"):
                        st.write(f"Internal links: {result.internal_links}")
                        st.write(f"External links: {result.external_links}")
                        st.write(f"Nofollow links: {result.nofollow_links}")

                    # Content
                    with st.expander(f"📄 Content ({result.word_count} words)"):
                        st.write(f"Paragraphs: {result.paragraph_count}")
                        st.write(f"Avg paragraph length: {result.avg_paragraph_length:.1f} words")

                    # Issues
                    if result.issues:
                        with st.expander(f"⚠️ Issues ({len(result.issues)})", expanded=True):
                            for issue in result.issues:
                                st.warning(issue)

                    # LLM Feedback
                    if result.llm_score is not None:
                        with st.expander("🤖 LLM Content Analysis", expanded=True):
                            st.metric("LLM Quality Score", f"{result.llm_score:.0f}/100")
                            if result.llm_feedback:
                                st.markdown(result.llm_feedback)

                except Exception as e:
                    st.error(f"Audit failed: {str(e)}")
                    status_text.text("❌ Audit failed")
            else:
                st.warning("Please enter a URL to audit")

    # --- SERP Tracker Sub-tab ---
    with seo_tab2:
        st.markdown("### SERP Position Tracker")
        st.caption("Track keyword rankings in search results")

        serp_keyword = st.text_input("Keyword to track", placeholder="seo tools")
        col1, col2 = st.columns(2)
        with col1:
            serp_engine = st.selectbox("Search Engine", ["ddg", "google"], key="serp_engine")
        with col2:
            serp_results = st.slider("Number of results", MIN_SERP_RESULTS, MAX_SERP_RESULTS, DEFAULT_SERP_RESULTS)

        track_domain = st.text_input("Track specific domain (optional)", placeholder="example.com")

        if st.button("Track SERP", type="primary"):
            if serp_keyword:
                with st.spinner(f"🔍 Tracking SERP positions for '{serp_keyword}'..."):
                    try:
                        tracker = get_serp_tracker()(
                            google_api_key=settings.get("google_cse_key", ""),
                            google_cx=settings.get("google_cse_cx", "")
                        )

                        snapshot = tracker.track_keyword(
                            serp_keyword,
                            engine=serp_engine,
                            max_results=serp_results
                        )

                        st.success(f"✅ Tracked {len(snapshot.results)} results for '{serp_keyword}'")
                        st.toast(f"SERP tracked: {len(snapshot.results)} results", icon="🔍")

                        # Display results
                        if snapshot.results:
                            results_data = []
                            for r in snapshot.results:
                                results_data.append({
                                    "Position": r.position,
                                    "Title": r.title,
                                    "URL": r.url,
                                    "Snippet": r.snippet[:100] + "..." if len(r.snippet) > 100 else r.snippet
                                })

                            st.dataframe(pd.DataFrame(results_data), use_container_width=True)

                            # Domain position check
                            if track_domain:
                                domain_pos = next((r.position for r in snapshot.results if track_domain in r.url), None)
                                if domain_pos:
                                    st.info(f"✅ Domain '{track_domain}' found at position {domain_pos}")
                                else:
                                    st.warning(f"❌ Domain '{track_domain}' not found in top {len(snapshot.results)} results")

                            # Export
                            if st.button("Export SERP Snapshot"):
                                path = tracker.export_to_csv(
                                    [snapshot],
                                    os.path.join(out_dir, f"serp_{serp_keyword.replace(' ', '_')}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv")
                                )
                                st.success(f"Exported to {path}")

                    except Exception as e:
                        st.error(f"SERP tracking failed: {str(e)}")
            else:
                st.warning("Please enter a keyword to track")

    # --- Site Extractor Sub-tab ---
    with seo_tab3:
        st.markdown("### Site to Markdown Extractor")
        st.caption("Extract entire websites or sitemaps to markdown files")

        extraction_mode = st.radio("Extraction Mode", ["Sitemap URL", "Domain Crawl"])

        if extraction_mode == "Sitemap URL":
            sitemap_url = st.text_input("Sitemap URL", placeholder="https://example.com/sitemap.xml")
            max_sitemap_pages = st.number_input("Max pages", min_value=MIN_SITEMAP_PAGES, max_value=MAX_SITEMAP_PAGES, value=DEFAULT_SITEMAP_PAGES)

            if st.button("Extract from Sitemap", type="primary"):
                if sitemap_url:
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    try:
                        extractor = get_site_extractor()(
                            timeout=int(settings.get("fetch_timeout", 15)),
                            concurrency=int(settings.get("concurrency", 8))
                        )

                        status_text.text("🗺️ Parsing sitemap...")
                        progress_bar.progress(0.15)

                        status_text.text(f"🌐 Fetching up to {max_sitemap_pages} pages...")
                        progress_bar.progress(0.4)

                        status_text.text("📄 Converting to markdown...")
                        progress_bar.progress(0.6)

                        pages = extractor.sync_extract_sitemap(sitemap_url, max_pages=max_sitemap_pages)

                        if pages:
                            status_text.text("💾 Saving markdown files...")
                            progress_bar.progress(0.85)

                            domain = urlparse(sitemap_url).netloc
                            output_dir = extractor.save_to_files(pages, domain)

                            progress_bar.progress(1.0)
                            status_text.text("✓ Extraction complete!")
                            st.success(f"✅ Extracted {len(pages)} pages from sitemap")
                            st.info(f"📁 Files saved in: `{output_dir}`")
                            st.toast(f"Extracted {len(pages)} pages", icon="📄")
                        else:
                            st.warning("No pages extracted from sitemap")

                    except Exception as e:
                        st.error(f"Extraction failed: {str(e)}")
                        status_text.text("❌ Extraction failed")
                else:
                    st.warning("Please enter a sitemap URL")

        else:  # Domain Crawl
            domain_url = st.text_input("Domain URL", placeholder="https://example.com")
            max_crawl_pages = st.number_input("Max pages to crawl", min_value=MIN_SITE_CRAWL_PAGES, max_value=MAX_SITE_CRAWL_PAGES, value=DEFAULT_SITE_CRAWL_PAGES)
            deep_crawl_site = st.checkbox("Deep crawl (slower, more thorough)", value=True)

            if st.button("Extract from Domain", type="primary"):
                if domain_url:
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    try:
                        extractor = get_site_extractor()(
                            timeout=int(settings.get("fetch_timeout", 15)),
                            concurrency=int(settings.get("concurrency", 8))
                        )

                        status_text.text("🕷️ Starting domain crawl...")
                        progress_bar.progress(0.1)

                        status_text.text(f"🌐 Crawling up to {max_crawl_pages} pages...")
                        progress_bar.progress(0.3)

                        status_text.text("📄 Converting HTML to markdown...")
                        progress_bar.progress(0.6)

                        pages = extractor.sync_extract_domain(
                            domain_url,
                            max_pages=max_crawl_pages,
                            deep_crawl=deep_crawl_site
                        )

                        if pages:
                            status_text.text("💾 Saving markdown files...")
                            progress_bar.progress(0.85)

                            domain = urlparse(domain_url).netloc
                            output_dir = extractor.save_to_files(pages, domain)

                            progress_bar.progress(1.0)
                            status_text.text("✓ Domain extraction complete!")
                            st.success(f"✅ Extracted {len(pages)} pages from {domain}")
                            st.info(f"📁 Files saved in: `{output_dir}`")
                            st.toast(f"Extracted {len(pages)} pages", icon="🕷️")
                        else:
                            st.warning("No pages extracted from domain")

                    except Exception as e:
                        st.error(f"Extraction failed: {str(e)}")
                        status_text.text("❌ Extraction failed")
                else:
                    st.warning("Please enter a domain URL")
