"""
Audit Tab - Client onboarding and site audits
"""

import streamlit as st
import asyncio
import httpx
from pathlib import Path
from config.loader import ConfigLoader
from llm.adapter import LLMAdapter
from audit.page_audit import audit_page
from audit.quick_wins import generate_quick_wins
from onboarding.wizard import run_onboarding
from constants import (MIN_ONBOARD_CRAWL_PAGES, MAX_ONBOARD_CRAWL_PAGES, DEFAULT_ONBOARD_CRAWL_PAGES,
                       MIN_ONBOARD_AUDIT_PAGES, MAX_ONBOARD_AUDIT_PAGES, DEFAULT_ONBOARD_AUDIT_PAGES)


def get_llm_adapter():
    """Helper function to create LLM adapter"""
    config_loader = ConfigLoader()
    config = config_loader.get_merged_config()
    return LLMAdapter.from_config(config)


def render_audit_tab(settings: dict, out_dir: str):
    """
    Render the Audit tab

    Args:
        settings: Application settings dict
        out_dir: Output directory path
    """
    st.subheader("Client Onboarding & Audit")
    st.caption("Run comprehensive site audits and generate prioritized quick wins")

    st.markdown("### Onboarding Mode")
    st.caption("Automated workflow: Crawl → Audit → Quick Wins")

    domain_input = st.text_input("Client Domain", placeholder="https://client-site.com")

    col1, col2 = st.columns(2)
    with col1:
        max_crawl_pages_onboard = st.slider("Max pages to crawl", MIN_ONBOARD_CRAWL_PAGES, MAX_ONBOARD_CRAWL_PAGES, DEFAULT_ONBOARD_CRAWL_PAGES, key="onboard_crawl")
    with col2:
        max_audit_pages_onboard = st.slider("Pages to audit", MIN_ONBOARD_AUDIT_PAGES, MAX_ONBOARD_AUDIT_PAGES, DEFAULT_ONBOARD_AUDIT_PAGES, key="onboard_audit")

    if st.button("🚀 Run Onboarding Wizard", type="primary"):
        if domain_input:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            try:
                adapter = get_llm_adapter()

                # Multi-phase progress
                status_text.text("🕷️ Step 1/4: Crawling site...")
                progress_bar.progress(0.1)

                # Prepare output directory
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "audits"

                status_text.text(f"🕷️ Crawling up to {max_crawl_pages_onboard} pages...")
                progress_bar.progress(0.25)

                status_text.text("🔍 Step 2/4: Auditing pages...")
                progress_bar.progress(0.4)

                status_text.text(f"📊 Analyzing {max_audit_pages_onboard} pages with LLM...")
                progress_bar.progress(0.6)

                status_text.text("⚡ Step 3/4: Generating quick wins...")
                progress_bar.progress(0.75)

                status_text.text("💾 Step 4/4: Saving audit report...")
                progress_bar.progress(0.85)

                # Run onboarding
                with st.spinner("🤖 Running comprehensive site analysis..."):
                    result = asyncio.run(run_onboarding(
                        domain=domain_input,
                        llm_adapter=adapter,
                        max_crawl_pages=max_crawl_pages_onboard,
                        max_audit_pages=max_audit_pages_onboard,
                        output_dir=out_path,
                        concurrency=int(settings.get("concurrency", 8))
                    ))

                st.session_state["audit_result"] = result

                progress_bar.progress(1.0)
                status_text.text("✓ Onboarding workflow complete!")
                success_message = (
                    f"✅ Audited {len(result.audits)} pages, generated {len(result.all_quick_wins)} prioritized quick wins"
                )
                if result.failed_urls:
                    success_message += f" (⚠️ {len(result.failed_urls)} page(s) skipped due to errors)"
                st.success(success_message)

                if result.failed_urls:
                    skipped_list = "\n".join(f"• {url}" for url in result.failed_urls)
                    st.warning(
                        "Some pages could not be audited successfully. "
                        "They may have timed out or returned an error:\n" + skipped_list
                    )
                    st.toast("Audit completed with some skipped pages", icon="⚠️")
                else:
                    st.toast("Audit complete!", icon="🔍")

            except Exception as e:
                st.error(f"Onboarding failed: {str(e)}")
                status_text.text("❌ Onboarding failed")
        else:
            st.warning("Please enter a domain")

    st.divider()
    st.markdown("### Single Page Audit")
    st.caption("Audit a specific page with LLM-enhanced analysis")

    audit_url_single = st.text_input("Page URL", placeholder="https://example.com/page")

    if st.button("🔍 Audit Page"):
        if audit_url_single:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            try:
                adapter = get_llm_adapter()

                # Fetch page
                status_text.text("🌐 Fetching page...")
                progress_bar.progress(0.2)

                resp = httpx.get(audit_url_single, timeout=15, follow_redirects=True,
                                headers={"User-Agent": "LeadHunter/1.0"})
                resp.raise_for_status()
                html = resp.text

                # Audit
                status_text.text("📊 Analyzing content and technical SEO...")
                progress_bar.progress(0.5)

                status_text.text("🤖 Running LLM content analysis...")
                progress_bar.progress(0.7)

                page_audit = audit_page(
                    url=audit_url_single,
                    html_content=html,
                    llm_adapter=adapter,
                    use_llm=True
                )

                # Store in a list for compatibility with onboarding result
                st.session_state["single_audit"] = page_audit

                progress_bar.progress(1.0)
                status_text.text("✓ Audit complete!")
                st.success(f"✅ Page audit complete! Score: {page_audit.score}/100, Grade: {page_audit.grade}")
                st.toast("Page analyzed!", icon="✅")

            except Exception as e:
                st.error(f"Audit failed: {str(e)}")
                status_text.text("❌ Audit failed")

    # Display onboarding results
    if st.session_state.get("audit_result"):
        result = st.session_state["audit_result"]

        st.divider()
        st.subheader(f"📊 Audit Results: {result.domain}")

        st.info(f"Crawled: {result.pages_crawled} pages | Audited: {result.pages_audited} pages")

        if result.failed_urls:
            st.warning(
                "The following page(s) could not be audited and were skipped:\n" +
                "\n".join(f"• {url}" for url in result.failed_urls)
            )

        if not result.audits:
            st.error(
                "No audits were completed successfully. Please verify the domain is accessible "
                "and try again with fewer pages or a higher timeout."
            )
            return

        # Page audits
        for i, audit in enumerate(result.audits, 1):
            with st.expander(f"📄 {audit.url} (Score: {audit.score}/100, Grade: {audit.grade})", expanded=(i==1)):
                # Score metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall", f"{audit.score}/100")
                with col2:
                    st.metric("Content", f"{audit.content_score}/100")
                with col3:
                    st.metric("Technical", f"{audit.technical_score}/100")
                with col4:
                    st.metric("SEO", f"{audit.seo_score}/100")

                # Issues
                if audit.issues:
                    st.markdown("**⚠️ Issues:**")
                    for issue in audit.issues:
                        severity_color = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(issue.severity, "⚪")
                        st.caption(f"{severity_color} {issue.description}")

                # Strengths
                if audit.strengths:
                    st.markdown("**✅ Strengths:**")
                    for strength in audit.strengths:
                        st.caption(f"- {strength}")

        # Quick wins
        if result.all_quick_wins:
            st.divider()
            st.subheader(f"⚡ Top Quick Wins ({len(result.all_quick_wins)})")

            for i, task in enumerate(result.all_quick_wins, 1):
                with st.expander(f"{i}. {task.task.title} (Priority: {task.priority_score:.1f}/10)", expanded=(i<=3)):
                    st.markdown(f"**Action:** {task.task.action}")
                    st.markdown(f"**Expected Impact:** {task.task.impact}")
                    st.markdown(f"**Effort:** {task.task.effort}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Impact Score", f"{task.impact}/10")
                    with col2:
                        st.metric("Feasibility", f"{task.feasibility}/10")
                    with col3:
                        st.metric("Priority", f"{task.priority_score:.1f}/10")

    # Display single audit
    elif st.session_state.get("single_audit"):
        audit = st.session_state["single_audit"]

        st.divider()
        st.subheader(f"📊 Audit: {audit.url}")

        # Score metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall", f"{audit.score}/100")
            st.caption(f"Grade: {audit.grade}")
        with col2:
            st.metric("Content", f"{audit.content_score}/100")
        with col3:
            st.metric("Technical", f"{audit.technical_score}/100")
        with col4:
            st.metric("SEO", f"{audit.seo_score}/100")

        # Issues
        if audit.issues:
            with st.expander(f"⚠️ Issues ({len(audit.issues)})", expanded=True):
                for issue in audit.issues:
                    severity_color = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(issue.severity, "⚪")
                    st.markdown(f"{severity_color} **{issue.category}:** {issue.description}")

        # Strengths
        if audit.strengths:
            with st.expander(f"✅ Strengths ({len(audit.strengths)})", expanded=False):
                for strength in audit.strengths:
                    st.markdown(f"- {strength}")

        # Quick wins
        if audit.quick_wins:
            with st.expander(f"⚡ Quick Wins ({len(audit.quick_wins)})", expanded=True):
                for i, qw in enumerate(audit.quick_wins, 1):
                    st.markdown(f"**{i}. {qw.title}**")
                    st.caption(f"Action: {qw.action}")
                    st.caption(f"Impact: {qw.impact} | Effort: {qw.effort}")
                    st.divider()

        # Generate prioritized quick wins
        if st.button("Generate Prioritized Quick Wins"):
            tasks = generate_quick_wins(audit, max_wins=8)
            st.session_state["quick_wins_tasks"] = tasks
            st.success(f"Generated {len(tasks)} prioritized quick wins")

        # Display prioritized tasks
        if st.session_state.get("quick_wins_tasks"):
            st.divider()
            st.subheader("Prioritized Quick Wins")

            for i, task in enumerate(st.session_state["quick_wins_tasks"], 1):
                with st.expander(f"{i}. {task.task.title} (Priority: {task.priority_score:.1f}/10)", expanded=(i<=3)):
                    st.markdown(f"**Action:** {task.task.action}")
                    st.markdown(f"**Expected Impact:** {task.task.impact}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Impact", f"{task.impact:.1f}/10")
                    with col2:
                        st.metric("Feasibility", f"{task.feasibility:.1f}/10")
                    with col3:
                        st.metric("Priority", f"{task.priority_score:.1f}/10")
    else:
        st.info("Enter a domain to run onboarding or a page URL for single audit.")
