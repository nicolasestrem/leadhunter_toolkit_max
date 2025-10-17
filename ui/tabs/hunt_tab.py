"""
Hunt Tab - Search and extract leads from websites
"""

import streamlit as st
import asyncio
import datetime
import pandas as pd
from search import ddg_sites
from google_search import google_sites
from crawl import crawl_site
from extract import extract_basic
from fetch import text_content
from classify import classify_lead
from scoring import score_lead
from utils_html import domain_of
from ui.components.export_buttons import render_export_buttons
from ui.utils.session_state import get_results, set_results


def render_hunt_tab(settings: dict, default_keywords: dict):
    """Render the Hunt tab in the Streamlit UI.

    This function provides the user interface for searching and extracting leads from
    websites.

    Args:
        settings (dict): The current application settings.
        default_keywords (dict): The default keyword categories for classification.
    """
    # Extract parameters from settings
    from constants import DEFAULT_MAX_SITES, DEFAULT_MAX_PAGES, DEFAULT_FETCH_TIMEOUT, DEFAULT_CONCURRENCY

    max_sites = int(settings.get("max_sites", DEFAULT_MAX_SITES))
    max_pages = int(settings.get("max_pages", DEFAULT_MAX_PAGES))
    fetch_timeout = int(settings.get("fetch_timeout", DEFAULT_FETCH_TIMEOUT))
    concurrency = int(settings.get("concurrency", DEFAULT_CONCURRENCY))
    extract_emails = bool(settings.get("extract_emails", True))
    extract_phones = bool(settings.get("extract_phones", True))
    extract_social = bool(settings.get("extract_social", True))
    city = settings.get("city", "")
    deep_contact = bool(settings.get("deep_contact", True))

    st.subheader("Search and extract")
    q = st.text_input("Query example: plombier Toulouse site:.fr", placeholder="restaurants Berlin vegan")
    url_list = st.text_area("Or paste URLs to scan (one per line)")
    run = st.button("Run", type="primary")
    results = get_results()

    if run and (q or url_list.strip()):
        results = []
        urls = []

        # search switch
        if q:
            with st.spinner("Searching web..."):
                engine = settings.get("search_engine", "ddg")
                if engine == "google":
                    key = settings.get("google_cse_key", "")
                    cx = settings.get("google_cse_cx", "")
                    urls = google_sites(q, max_results=max_sites, api_key=key, cx=cx)
                    if not urls:
                        st.warning("Google selected but no results. Check your CSE key and cx.")
                else:
                    urls = ddg_sites(q, max_results=max_sites)
                if urls:
                    st.toast(f"Found {len(urls)} candidate sites", icon="🔍")

        if url_list.strip():
            pasted = [u.strip() for u in url_list.splitlines() if u.strip().startswith("http")]
            urls.extend(pasted)
            urls = list(dict.fromkeys(urls))

        # Progress tracking for crawling and extraction
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        crawl_settings = dict(settings)
        crawl_settings["extract_emails"] = extract_emails
        crawl_settings["extract_phones"] = extract_phones
        crawl_settings["extract_social"] = extract_social
        crawl_settings["city"] = city
        crawl_settings["deep_contact"] = deep_contact
        crawl_settings["max_pages"] = int(max_pages)

        # Phase 1: Crawling sites
        all_pages = {}
        total_sites = len(urls)

        for site_idx, u in enumerate(urls, 1):
            status_text.text(f"🕷️ Crawling site {site_idx}/{total_sites}: {u[:50]}...")
            progress_bar.progress(site_idx / (total_sites * 2))  # First half of progress

            try:
                pages = asyncio.run(crawl_site(
                    u,
                    timeout=int(fetch_timeout),
                    concurrency=int(concurrency),
                    max_pages=int(max_pages),
                    deep_contact=bool(deep_contact)
                ))
                all_pages.update(pages)
            except Exception as e:
                st.warning(f"Crawl error on {u}: {e}")

        st.toast(f"Crawled {len(all_pages)} pages from {total_sites} sites", icon="✅")

        # Phase 2: Extracting and classifying
        status_text.text(f"📊 Extracting contact information from {len(all_pages)} pages...")
        progress_bar.progress(0.5)

        by_domain = {}
        pages_processed = 0
        total_pages = len(all_pages)

        for page_url, html in all_pages.items():
            pages_processed += 1

            # Update every 10 pages or on last page
            if pages_processed % 10 == 0 or pages_processed == total_pages:
                status_text.text(f"📊 Extracting page {pages_processed}/{total_pages}...")
                progress_bar.progress(0.5 + (pages_processed / total_pages) * 0.4)

            # Extract contacts using basic extraction
            lead = extract_basic(page_url, html, crawl_settings)
            
            dom = lead.get("domain") or domain_of(page_url)
            if not dom:
                continue
            cur = by_domain.get(dom, {
                "domain": dom, "website": page_url, "emails": [], "phones": [], "social": {},
                "name": lead.get("name"), "tags": [], "status": "new", "notes": None,
                "city": lead.get("city"), "address": lead.get("address")
            })
            cur["website"] = cur.get("website") or page_url
            cur["name"] = cur.get("name") or lead.get("name")
            cur["emails"] = sorted(set((cur.get("emails") or []) + (lead.get("emails") or [])))
            cur["phones"] = sorted(set((cur.get("phones") or []) + (lead.get("phones") or [])))
            cur["address"] = cur.get("address") or lead.get("address")
            cur["city"] = cur.get("city") or lead.get("city")
            soc = cur.get("social") or {}
            for k, v in (lead.get("social") or {}).items():
                if v and not soc.get(k):
                    soc[k] = v
            cur["social"] = soc
            # Get text content for classification
            text = text_content(html)
            tags = classify_lead(text, default_keywords)
            cur["tags"] = sorted(set((cur.get("tags") or []) + tags))
            by_domain[dom] = cur

        # Phase 3: Scoring leads
        status_text.text(f"⭐ Scoring {len(by_domain)} leads...")
        progress_bar.progress(0.9)

        for dom, lead in by_domain.items():
            lead["score"] = score_lead(lead, crawl_settings)
            lead["when"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            results.append(lead)

        results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
        set_results(results)

        # Complete
        progress_bar.progress(1.0)
        status_text.text(f"✓ Complete! Found {len(results)} leads from {len(all_pages)} pages")
        avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
        st.success(f"✓ Hunt complete! Generated {len(results)} leads with average score: {avg_score:.1f}")
        st.balloons()

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)

        # Use export buttons component
        st.subheader("Export Results")
        render_export_buttons(results, namespace=settings.get("project", "default"))
