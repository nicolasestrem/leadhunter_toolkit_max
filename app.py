import streamlit as st
import asyncio, json, os, datetime, pandas as pd
from urllib.parse import urlparse
from pathlib import Path
from search import ddg_sites
from google_search import google_sites
from fetch import fetch_many, text_content, extract_links
from extract import extract_basic
from scoring import score_lead
from exporters import export_csv, export_json
from exporters_xlsx import export_xlsx
from utils_html import domain_of
from places import text_search as places_text_search, get_details as places_details
from crawl import crawl_site
from classify import classify_lead
from search_scraper import SearchScraper
from seo_audit import SEOAuditor
from serp_tracker import SERPTracker
from site_extractor import SiteExtractor
from llm_client import LLMClient
import httpx

# Consulting Pack imports
from config.loader import ConfigLoader
from llm.adapter import LLMAdapter
from leads.classify_score import classify_and_score_lead
from leads.contacts_extract import extract_contacts_from_markdown
from outreach.compose import compose_outreach
from dossier.build import build_dossier
from audit.page_audit import audit_page
from audit.quick_wins import generate_quick_wins
from onboarding.wizard import run_onboarding
from plugins import load_plugins, get_loaded_plugins, call_plugin_hook
from models import Lead
import zipfile

BASE = os.path.dirname(__file__)
SETTINGS_PATH = os.path.join(BASE, "settings.json")
PRESETS_DIR = os.path.join(BASE, "presets")
OUT_DIR = os.path.join(BASE, "out")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

DEFAULT_KEYWORDS = {
    "plumbing": ["plombier", "plomberie", "plumbing"],
    "restaurant": ["restaurant", "bistrot", "bistro", "cuisine"],
    "seo": ["seo", "référencement", "search engine"],
    "mobility": ["mobilité", "mobility", "transport", "vélo"]
}

def dict_to_json_safe(data):
    """
    Convert a dict with pandas/numpy types to JSON-serializable dict.

    Args:
        data: dict potentially containing Timestamp or numpy types

    Returns:
        Dict with JSON-serializable values
    """
    result = {}
    for key, value in data.items():
        if pd.isna(value):
            result[key] = None
        elif isinstance(value, pd.Timestamp):
            result[key] = value.isoformat()
        elif hasattr(value, 'item'):  # numpy types
            result[key] = value.item()
        else:
            result[key] = value
    return result

def dataframe_to_json_safe(df):
    """
    Convert DataFrame to JSON-serializable dict, handling Timestamps and other pandas types.

    Args:
        df: pandas DataFrame

    Returns:
        List of dicts with JSON-serializable values
    """
    # Convert to dict with default date format
    records = df.to_dict(orient="records")

    # Convert any remaining Timestamp objects to ISO strings
    return [dict_to_json_safe(record) for record in records]

def load_settings():
    try:
        return json.load(open(SETTINGS_PATH, "r", encoding="utf-8"))
    except Exception:
        return {}

def save_settings(data: dict):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_presets():
    items = []
    for name in os.listdir(PRESETS_DIR):
        if name.endswith(".json"):
            items.append(name[:-5])
    return sorted(items)

def load_preset(name: str) -> dict:
    path = os.path.join(PRESETS_DIR, name + ".json")
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return {}

def save_preset(name: str, data: dict):
    path = os.path.join(PRESETS_DIR, name + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="Lead Hunter Toolkit • Consulting Pack v1", layout="wide")
st.title("Lead Hunter Toolkit • Consulting Pack v1")

# Initialize plugins on first run
if 'plugins_loaded' not in st.session_state:
    try:
        st.session_state.plugins = load_plugins()
        st.session_state.plugins_loaded = True
        if st.session_state.plugins:
            st.toast(f"✓ Loaded {len(st.session_state.plugins)} plugins", icon="🔌")
    except Exception as e:
        st.error(f"Plugin loading error: {e}")
        st.session_state.plugins = []
        st.session_state.plugins_loaded = False
st.caption("Complete SMB consulting solution: Lead generation, AI-powered classification, personalized outreach, client dossiers, and comprehensive site audits.")

# ---- Top docs expander (flat indentation) ----
with st.expander("📚 Quick Start Guide", expanded=False):
    st.markdown("""
    ## Lead Hunter Toolkit • Consulting Pack v1

    ### 🎯 Complete Workflow

    **Step 1: Hunt** → Find leads through web search or paste URLs
    **Step 2: Classify** → Use AI to score leads (quality, fit, priority)
    **Step 3: Generate Outreach** → Create personalized messages in 3 variants
    **Step 4: Build Dossier** → Comprehensive analysis with quick wins
    **Step 5: Audit Site** → Technical SEO audit with recommendations
    **Step 6: Export Pack** → One-click export of all materials

    ---

    ### 🎯 Hunt Tab
    **Lead Generation & Discovery**
    - Search the web (DuckDuckGo or Google Custom Search)
    - Or paste URLs to scan directly
    - Smart BFS crawling with contact/about page prioritization
    - Extract emails, phones, social links automatically
    - Export to CSV, JSON, or XLSX

    ### 📊 Leads Tab (NEW!)
    **AI-Powered Classification & Scoring**
    - Multi-dimensional scoring: Quality, Fit, Priority (0-10)
    - Business type classification (restaurant, retail, services, etc.)
    - Issue flags detection (No SSL, thin content, poor mobile)
    - Quality signals identification
    - Advanced filtering by score and business type
    - Export to CSV, JSON, JSONL

    **Workflow:**
    1. Run Hunt to find leads
    2. Go to Leads tab
    3. Click "Classify All Leads" (uses LLM)
    4. Filter by scores and business type
    5. Select a lead for detailed actions

    ### ✉️ Outreach Tab (NEW!)
    **Personalized Message Generation**
    - Generate 3 message variants (problem, opportunity, quick-win angles)
    - Support for email, LinkedIn, SMS
    - Multilingual: English, French, German
    - Tone presets: Professional, Friendly, Direct
    - Deliverability checking (spam detection, word count, links)
    - Copy-to-clipboard buttons

    **Workflow:**
    1. Select a lead in Leads tab
    2. Go to Outreach tab
    3. Choose message type, language, tone
    4. Add optional dossier summary
    5. Generate 3 variants
    6. Review deliverability scores
    7. Export all variants

    ### 📋 Dossier Tab (NEW!)
    **RAG-Based Client Analysis**
    - Company overview with cited sources
    - Services/products identification
    - Digital presence analysis
    - Signals: Positive, Growth, Pain
    - Issues detected with severity
    - 48-hour quick wins (5 tasks)

    **Workflow:**
    1. Select a lead in Leads tab
    2. Go to Dossier tab
    3. Enter URLs to crawl OR paste content
    4. Generate dossier (uses LLM)
    5. Review all sections
    6. Export as Markdown or JSON

    ### 🔍 Audit Tab (NEW!)
    **Site Audits & Quick Wins**

    **Onboarding Wizard:**
    - Automated: Crawl → Audit → Quick Wins
    - Configurable page limits
    - Prioritized recommendations

    **Single Page Audit:**
    - LLM-enhanced analysis
    - Scores: Overall, Content, Technical, SEO
    - Issues by severity (critical, warning, info)
    - Strengths identification
    - Quick wins generation

    **Workflow:**
    1. Enter client domain
    2. Run Onboarding Wizard
    3. Review page audits and scores
    4. Check top quick wins
    5. Export report

    ### 📦 One-Click Export Pack (NEW!)
    **Complete Consulting Package**
    - Lead info (JSON)
    - Dossier (Markdown)
    - Outreach variants (Markdown)
    - Audit report (Markdown)
    - All packaged in a ZIP file

    **Workflow:**
    1. Complete Leads, Outreach, Dossier, Audit for a lead
    2. Go to Leads tab
    3. Select the lead
    4. Click "Create Export Pack"
    5. Share ZIP with client

    ---

    ### 🔍 Search Scraper Tab
    **AI-Powered Web Research**
    - Search and synthesize information from multiple sources
    - Two modes: AI Extraction (uses LLM) or Markdown (raw content)
    - Custom JSON schemas for structured extraction
    - Source attribution

    ### 🌍 Enrich with Places Tab
    - Google Places API integration
    - Search businesses by text query
    - Get structured data: name, address, website, phone

    ### ✏️ Review & Edit Tab
    - Edit leads in spreadsheet interface
    - Update status, tags, and notes
    - Summarize leads with LLM

    ### 🛠️ SEO Tools Tab
    - **Content Audit:** Meta tags, headings, images, links
    - **SERP Tracker:** Track keyword positions
    - **Site Extractor:** Convert sites to markdown

    ---

    ### ⚙️ Settings

    **LLM Integration (Required for Consulting Features):**
    - Works with LM Studio: `https://lm.leophir.com/`
    - Works with Ollama: `http://localhost:11434`
    - Works with any OpenAI-compatible endpoint
    - API key optional for local models
    - Automatic `/v1` path handling

    **Configuration:**
    - Project name for organized exports
    - Language, country, city for localization
    - Concurrency (6-8 recommended)
    - Fetch timeout and crawl settings

    **Presets:**
    - Save/load configurations per niche or location
    - Vertical presets available in `presets/verticals/`

    ---

    ### 💡 Best Practices

    **For Consultants:**
    1. Use presets for each vertical (restaurant, retail, services)
    2. Always classify leads before outreach
    3. Build dossier before first contact
    4. Include dossier summary in outreach
    5. Run audit during discovery call
    6. Use export pack for client delivery

    **Performance:**
    - Keep concurrency low (6-8) to respect target sites
    - Use local LLM for privacy and cost savings
    - LM Studio recommended for best quality

    **Multilingual:**
    - Set language in settings (EN, FR, DE)
    - Outreach will use language-specific tone presets
    - Dossier and audit work in any language
    """)

# ---- Sidebar ----
with st.sidebar:
    st.header("Settings")
    s = load_settings()

    search_engine = st.selectbox(
        "Search engine",
        ["ddg", "google"],
        index=0 if s.get("search_engine", "ddg") == "ddg" else 1
    )

    project = st.text_input("Project name", s.get("project", "default"))
    country = st.text_input("Country code", s.get("country", "fr"))
    language = st.text_input("Language", s.get("language", "fr-FR"))
    city = st.text_input("City focus", s.get("city", "Toulouse"))
    radius_km = st.number_input("Radius km", min_value=0, max_value=500, value=int(s.get("radius_km", 50)))
    max_sites = st.slider("Max sites to scan (per query)", 1, 200, int(s.get("max_sites", 25)))
    fetch_timeout = st.slider("Fetch timeout seconds", 5, 60, int(s.get("fetch_timeout", 15)))
    concurrency = st.slider("Concurrency", 1, 32, int(s.get("concurrency", 8)))
    deep_contact = st.checkbox("Deep crawl contact/about pages", value=bool(s.get("deep_contact", True)))
    max_pages = st.slider("Max pages per site", 1, 20, int(s.get("max_pages", 5)))
    extract_emails = st.checkbox("Extract emails", value=bool(s.get("extract_emails", True)))
    extract_phones = st.checkbox("Extract phones", value=bool(s.get("extract_phones", True)))
    extract_social = st.checkbox("Extract social links", value=bool(s.get("extract_social", True)))

    # Google Places
    g_api = st.text_input("Google Places API key", value=s.get("google_places_api_key", ""), type="password")
    g_region = st.text_input("Places region", value=s.get("google_places_region", "FR"))
    g_lang = st.text_input("Places language", value=s.get("google_places_language", "fr"))

    # Google CSE
    g_cse_key = st.text_input("Google CSE API key", value=s.get("google_cse_key", ""), type="password")
    g_cx = st.text_input("Google CSE cx (engine id)", value=s.get("google_cse_cx", ""))

    st.subheader("LLM")
    llm_base = st.text_input("LLM base URL (OpenAI compatible)", s.get("llm_base", ""))
    llm_key = st.text_input("LLM API key", value=s.get("llm_key", ""), type="password")
    llm_model = st.text_input("LLM model", s.get("llm_model", "gpt-4o-mini"))

    with st.expander("Advanced LLM Settings"):
        llm_temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=float(s.get("llm_temperature", 0.2)),
            step=0.1,
            help="Controls randomness: 0.0 = deterministic, 2.0 = very creative"
        )
        llm_max_tokens = st.number_input(
            "Max tokens (0 = unlimited)",
            min_value=0,
            max_value=128000,
            value=int(s.get("llm_max_tokens", 0)),
            help="Maximum tokens in LLM response. Important for local models to prevent timeouts."
        )

    if st.button("Save settings"):
        s.update({
            "search_engine": search_engine,
            "project": project,
            "country": country,
            "language": language,
            "city": city,
            "radius_km": radius_km,
            "max_sites": max_sites,
            "fetch_timeout": fetch_timeout,
            "concurrency": concurrency,
            "deep_contact": deep_contact,
            "max_pages": max_pages,
            "extract_emails": extract_emails,
            "extract_phones": extract_phones,
            "extract_social": extract_social,
            "google_places_api_key": g_api,
            "google_places_region": g_region,
            "google_places_language": g_lang,
            "google_cse_key": g_cse_key,
            "google_cse_cx": g_cx,
            "llm_base": llm_base,
            "llm_key": llm_key,
            "llm_model": llm_model,
            "llm_temperature": llm_temperature,
            "llm_max_tokens": llm_max_tokens
        })
        save_settings(s)
        st.success("Saved.")

    st.divider()
    st.subheader("Vertical Presets")
    st.caption("Industry-specific scoring and outreach optimization")

    # Get available verticals
    verticals_dir = Path(__file__).parent / "presets" / "verticals"
    available_verticals = []
    if verticals_dir.exists():
        available_verticals = [
            f.stem for f in verticals_dir.glob("*.yml")
        ]

    # Get currently active vertical
    config_loader = ConfigLoader()
    active_vertical = config_loader.get_active_vertical()

    # Show current status
    if active_vertical:
        st.info(f"✓ Active vertical: **{active_vertical}**")
    else:
        st.caption("No vertical preset active (using default settings)")

    # Vertical selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_vertical = st.selectbox(
            "Select vertical",
            ["None"] + available_verticals,
            index=0 if not active_vertical else (
                available_verticals.index(active_vertical) + 1
                if active_vertical in available_verticals else 0
            ),
            help="Apply industry-specific scoring weights and outreach templates"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Apply", key="apply_vertical"):
            # Update settings with new vertical
            new_vertical = None if selected_vertical == "None" else selected_vertical
            s["active_vertical"] = new_vertical
            save_settings(s)

            # Reload config to apply changes
            config_loader.reload()

            if new_vertical:
                st.success(f"Applied vertical: {new_vertical}")
            else:
                st.success("Cleared vertical preset")
            st.rerun()

    # Show vertical details if active
    if active_vertical and active_vertical in available_verticals:
        vertical_config = config_loader.load_vertical_preset(active_vertical)
        if vertical_config:
            with st.expander("Vertical Details"):
                st.caption(f"**Description**: {vertical_config.get('description', 'N/A')}")

                # Show scoring weights
                scoring = vertical_config.get('scoring', {})
                if scoring:
                    st.caption("**Scoring Weights**:")
                    for key, value in scoring.items():
                        st.caption(f"  • {key}: {value}")

                # Show outreach focus
                outreach = vertical_config.get('outreach', {})
                if outreach:
                    focus_areas = outreach.get('focus_areas', [])
                    if focus_areas:
                        st.caption(f"**Focus Areas**: {', '.join(focus_areas[:3])}{'...' if len(focus_areas) > 3 else ''}")

    st.divider()
    st.subheader("Plugins")
    st.caption("Extend functionality with custom plugins")

    # Get loaded plugins
    loaded_plugins = st.session_state.get('plugins', [])

    if loaded_plugins:
        st.info(f"✓ {len(loaded_plugins)} plugin(s) loaded")

        # Show plugin details in expander
        with st.expander("Plugin Details", expanded=False):
            for plugin in loaded_plugins:
                st.markdown(f"**{plugin.get('name', 'Unknown')}** v{plugin.get('version', '0.0.0')}")
                st.caption(plugin.get('description', 'No description'))

                # Show hooks
                hooks = plugin.get('hooks', {})
                if hooks:
                    st.caption(f"Hooks: {', '.join(hooks.keys())}")

                # Show author if available
                if 'author' in plugin:
                    st.caption(f"Author: {plugin['author']}")

                st.markdown("---")
    else:
        st.caption("No plugins loaded")

    # Reload plugins button
    if st.button("Reload Plugins", help="Reload all plugins from plugins/ directory"):
        try:
            st.session_state.plugins = load_plugins()
            st.session_state.plugins_loaded = True
            st.success(f"Reloaded {len(st.session_state.plugins)} plugins")
            st.rerun()
        except Exception as e:
            st.error(f"Error reloading plugins: {e}")

    st.divider()
    st.subheader("Presets")
    st.caption("Save/load configurations per niche or location")

    presets = list_presets()

    col1, col2 = st.columns(2)
    with col1:
        selected_preset = st.selectbox("Load preset", [""] + presets)
    with col2:
        if selected_preset:
            if st.button("Load"):
                preset_data = load_preset(selected_preset)
                if preset_data:
                    s.update(preset_data)
                    save_settings(s)
                    st.success(f"Loaded preset: {selected_preset}")
                    st.rerun()

    preset_name = st.text_input("Save as preset", placeholder="berlin_plumbers")
    if st.button("Save preset"):
        if preset_name:
            save_preset(preset_name, s)
            st.success(f"Saved preset: {preset_name}")
        else:
            st.warning("Please enter a preset name")

    if selected_preset:
        if st.button("Delete preset", type="secondary"):
            try:
                preset_path = os.path.join(PRESETS_DIR, selected_preset + ".json")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    st.success(f"Deleted preset: {selected_preset}")
                    st.rerun()
            except Exception as e:
                st.error(f"Error deleting preset: {e}")

    st.divider()
    st.subheader("Cache Management")
    st.caption("Manage HTTP response cache")

    # Import cache manager
    from cache_manager import get_cache_stats, cleanup_cache, clear_all_cache

    try:
        cache_stats = get_cache_stats()
        st.metric("Cache Files", f"{cache_stats['file_count']} files")
        st.metric("Cache Size", f"{cache_stats['total_size_mb']:.1f} MB")
        st.caption(f"Max size: {cache_stats['max_size_mb']} MB • Max age: {cache_stats['max_age_days']} days")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cleanup Expired", help="Remove expired cache files"):
                result = cleanup_cache()
                st.success(f"Removed {result['expired_deleted']} expired files and {result['size_deleted']} oversized files")
                st.rerun()
        with col2:
            if st.button("Clear All Cache", type="secondary", help="Delete all cached files"):
                deleted = clear_all_cache()
                st.success(f"Cleared cache: {deleted} files deleted")
                st.rerun()
    except Exception as e:
        st.error(f"Cache error: {e}")

    st.divider()
    # Advanced Export Section
    from export_sidebar import render_export_sidebar
    render_export_sidebar(project)
    exp_placeholder = st.empty()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Hunt", "Leads", "Outreach", "Dossier", "Audit",
    "Search Scraper", "Enrich with Places", "Review & Edit", "SEO Tools", "Session"
])

# Initialize session state
if "results" not in st.session_state:
    st.session_state["results"] = []
if "search_scraper_result" not in st.session_state:
    st.session_state["search_scraper_result"] = None
if "classified_leads" not in st.session_state:
    st.session_state["classified_leads"] = []
if "selected_lead" not in st.session_state:
    st.session_state["selected_lead"] = None
if "outreach_result" not in st.session_state:
    st.session_state["outreach_result"] = None
if "dossier_result" not in st.session_state:
    st.session_state["dossier_result"] = None
if "audit_result" not in st.session_state:
    st.session_state["audit_result"] = None

# ---------------------- HUNT TAB ----------------------
with tab1:
    st.subheader("Search and extract")
    q = st.text_input("Query example: plombier Toulouse site:.fr", placeholder="restaurants Berlin vegan")
    url_list = st.text_area("Or paste URLs to scan (one per line)")
    run = st.button("Run", type="primary")
    results = st.session_state["results"]

    if run and (q or url_list.strip()):
        results = []
        urls = []

        # search switch
        if q:
            with st.spinner("Searching web..."):
                engine = s.get("search_engine", "ddg")
                if engine == "google":
                    key = s.get("google_cse_key", "")
                    cx = s.get("google_cse_cx", "")
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

        settings = dict(s)
        settings["extract_emails"] = extract_emails
        settings["extract_phones"] = extract_phones
        settings["extract_social"] = extract_social
        settings["city"] = city
        settings["deep_contact"] = deep_contact
        settings["max_pages"] = int(max_pages)

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

            lead = extract_basic(page_url, html, settings)
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
            cur["city"] = cur.get("city") or lead.get("city")
            cur["address"] = cur.get("address") or lead.get("address")
            soc = cur.get("social") or {}
            for k, v in (lead.get("social") or {}).items():
                if v and not soc.get(k):
                    soc[k] = v
            cur["social"] = soc
            text = text_content(html)
            tags = classify_lead(text, DEFAULT_KEYWORDS)
            cur["tags"] = sorted(set((cur.get("tags") or []) + tags))
            by_domain[dom] = cur

        # Phase 3: Scoring leads
        status_text.text(f"⭐ Scoring {len(by_domain)} leads...")
        progress_bar.progress(0.9)

        for dom, lead in by_domain.items():
            lead["score"] = score_lead(lead, settings)
            lead["when"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            results.append(lead)

        results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
        st.session_state["results"] = results

        # Complete
        progress_bar.progress(1.0)
        status_text.text(f"✓ Complete! Found {len(results)} leads from {len(all_pages)} pages")
        st.success(f"✓ Hunt complete! Generated {len(results)} leads with average score: {sum(r.get('score', 0) for r in results) / len(results):.1f}")
        st.balloons()

    if results:
        st.dataframe(pd.DataFrame(results), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Export CSV"):
                path = export_csv(results)
                exp_placeholder.info(f"Saved CSV at {path}")
        with c2:
            if st.button("Export JSON"):
                path = export_json(results)
                exp_placeholder.info(f"Saved JSON at {path}")
        with c3:
            if st.button("Export XLSX"):
                path = export_xlsx(results)
                exp_placeholder.info(f"Saved XLSX at {path}")

# ---------------------- LEADS TAB ----------------------
with tab2:
    st.subheader("Lead Classification & Scoring")
    st.caption("Classify and score leads with multi-dimensional analysis using LLM")

    # Helper function to create LLM adapter
    def get_llm_adapter():
        config_loader = ConfigLoader()
        config = config_loader.get_merged_config()
        return LLMAdapter.from_config(config)

    # Check if we have leads from Hunt tab
    if st.session_state.get("results"):
        st.info(f"Found {len(st.session_state['results'])} leads from Hunt tab. Classify them below.")

        col1, col2 = st.columns([3, 1])
        with col1:
            use_llm_classify = st.checkbox("Use LLM for classification", value=True,
                                          help="Enable LLM to classify business type and detect issues")
        with col2:
            if st.button("Classify All Leads", type="primary"):
                # Progress tracking
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                start_time = datetime.datetime.now()

                try:
                    # Get LLM adapter if enabled
                    adapter = get_llm_adapter() if use_llm_classify else None

                    classified = []
                    total_leads = len(st.session_state["results"])

                    for i, lead in enumerate(st.session_state["results"]):
                        # Calculate estimated time remaining
                        if i > 0:
                            elapsed = (datetime.datetime.now() - start_time).total_seconds()
                            avg_time_per_lead = elapsed / i
                            remaining_leads = total_leads - i
                            est_remaining = avg_time_per_lead * remaining_leads
                            eta_text = f" (ETA: {int(est_remaining)}s)"
                        else:
                            eta_text = ""

                        status_text.text(f"🔍 Classifying lead {i+1}/{total_leads}: {lead.get('name', 'Unknown')[:40]}...{eta_text}")
                        progress_bar.progress((i + 1) / total_leads)

                        # Get content sample (combine available text)
                        content_parts = []
                        if lead.get("name"):
                            content_parts.append(f"Company: {lead['name']}")
                        if lead.get("domain"):
                            content_parts.append(f"Domain: {lead['domain']}")
                        if lead.get("notes"):
                            content_parts.append(lead["notes"])
                        content_sample = " ".join(content_parts)

                        # Classify and score (convert dict to Lead object)
                        try:
                            lead_obj = Lead(**lead)
                        except Exception as e:
                            st.warning(f"Invalid lead data: {e}")
                            continue

                        lead_record = classify_and_score_lead(
                            lead=lead_obj,
                            llm_adapter=adapter,
                            content_sample=content_sample,
                            use_llm=use_llm_classify
                        )
                        classified.append(lead_record.dict())

                    st.session_state["classified_leads"] = classified

                    # Complete
                    status_text.text(f"✓ Classification complete!")
                    elapsed_total = (datetime.datetime.now() - start_time).total_seconds()
                    st.success(f"✅ Classified {len(classified)} leads in {elapsed_total:.1f}s (avg {elapsed_total/len(classified):.1f}s per lead)")
                    st.toast(f"Classified {len(classified)} leads", icon="✅")

                except Exception as e:
                    st.error(f"Classification failed: {str(e)}")
                    status_text.text("❌ Classification failed")

    # Display classified leads
    if st.session_state.get("classified_leads"):
        df = pd.DataFrame(st.session_state["classified_leads"])

        # Filters
        st.subheader("Filters")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_quality = st.slider("Min Quality Score", 0.0, 10.0, 0.0)
        with col2:
            min_fit = st.slider("Min Fit Score", 0.0, 10.0, 0.0)
        with col3:
            min_priority = st.slider("Min Priority Score", 0.0, 10.0, 0.0)
        with col4:
            business_types = df["business_type"].unique().tolist() if "business_type" in df.columns else []
            selected_types = st.multiselect("Business Type", business_types, default=business_types)

        # Apply filters
        filtered_df = df.copy()
        if "score_quality" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_quality"] >= min_quality]
        if "score_fit" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_fit"] >= min_fit]
        if "score_priority" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_priority"] >= min_priority]
        if selected_types and "business_type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["business_type"].isin(selected_types)]

        # Display
        st.subheader(f"Results ({len(filtered_df)} leads)")

        # Select columns to display
        display_cols = ["name", "domain", "score_quality", "score_fit", "score_priority",
                       "business_type", "emails", "phones", "issue_flags", "quality_signals"]
        display_cols = [col for col in display_cols if col in filtered_df.columns]

        st.dataframe(filtered_df[display_cols], use_container_width=True)

        # Lead selection for detailed actions
        st.subheader("Lead Actions")
        lead_names = [f"{row.get('name', 'Unknown')} ({row.get('domain', 'N/A')})"
                     for _, row in filtered_df.iterrows()]

        if lead_names:
            selected_idx = st.selectbox("Select lead for detailed actions", range(len(lead_names)),
                                       format_func=lambda x: lead_names[x])
            st.session_state["selected_lead"] = dict_to_json_safe(filtered_df.iloc[selected_idx].to_dict())

            st.info(f"**Selected:** {lead_names[selected_idx]}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quality", f"{st.session_state['selected_lead'].get('score_quality', 0):.1f}/10")
            with col2:
                st.metric("Fit", f"{st.session_state['selected_lead'].get('score_fit', 0):.1f}/10")
            with col3:
                st.metric("Priority", f"{st.session_state['selected_lead'].get('score_priority', 0):.1f}/10")

            # One-Click Pack Export
            st.divider()
            st.markdown("### 📦 One-Click Export Pack")
            st.caption("Export complete consulting package: Dossier + Audit + Outreach variants")

            if st.button("📦 Create Export Pack", type="primary", use_container_width=True):
                with st.status("Creating export pack...", expanded=True) as status:
                    try:
                        selected_lead = st.session_state["selected_lead"]
                        project = s.get("project", "default")
                        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                        company_slug = selected_lead.get('name', 'unknown').replace(' ', '_')

                        # Create pack directory
                        pack_dir = Path(OUT_DIR) / project / f"pack_{company_slug}_{timestamp}"
                        pack_dir.mkdir(parents=True, exist_ok=True)

                        status.update(label="Collecting materials...")

                        # 1. Save lead info
                        with open(pack_dir / "lead_info.json", "w", encoding="utf-8") as f:
                            json.dump(selected_lead, f, ensure_ascii=False, indent=2)

                        # 2. Save dossier if available
                        if st.session_state.get("dossier_result"):
                            status.update(label="Adding dossier...")
                            dossier = st.session_state["dossier_result"]

                            # Markdown
                            dossier_md = f"# Client Dossier: {dossier.company_name}\n\n"
                            dossier_md += f"**Website:** {dossier.website}\n\n"
                            dossier_md += f"## Company Overview\n\n{dossier.company_overview}\n\n"
                            dossier_md += f"## Services & Products\n\n"
                            for item in dossier.services_products:
                                dossier_md += f"- {item}\n"
                            dossier_md += f"\n## Digital Presence\n\n"
                            dossier_md += f"**Website Quality:** {dossier.digital_presence.website_quality}\n\n"
                            if dossier.digital_presence.social_platforms:
                                dossier_md += "**Social Platforms:**\n"
                                for platform in dossier.digital_presence.social_platforms:
                                    dossier_md += f"- {platform}\n"
                            dossier_md += f"\n## Quick Wins\n\n"
                            for i, qw in enumerate(dossier.quick_wins, 1):
                                dossier_md += f"### {i}. {qw.title}\n\n"
                                dossier_md += f"**Action:** {qw.action}\n\n"
                                dossier_md += f"**Impact:** {qw.impact} | **Effort:** {qw.effort} | **Priority:** {qw.priority:.1f}/10\n\n"

                            with open(pack_dir / "dossier.md", "w", encoding="utf-8") as f:
                                f.write(dossier_md)

                        # 3. Save outreach if available
                        if st.session_state.get("outreach_result"):
                            status.update(label="Adding outreach variants...")
                            outreach = st.session_state["outreach_result"]

                            outreach_md = f"# Outreach Variants: {outreach.company_name}\n\n"
                            outreach_md += f"**Type:** {outreach.message_type} | **Language:** {outreach.language} | **Tone:** {outreach.tone}\n\n"

                            for i, variant in enumerate(outreach.variants, 1):
                                outreach_md += f"## Variant {i}: {variant.angle.title()}\n\n"
                                if variant.subject:
                                    outreach_md += f"**Subject:** {variant.subject}\n\n"
                                outreach_md += f"**Message:**\n\n{variant.body}\n\n"
                                if variant.cta:
                                    outreach_md += f"**CTA:** {variant.cta}\n\n"
                                outreach_md += f"**Deliverability:** {variant.deliverability_score}/100\n\n"
                                outreach_md += "---\n\n"

                            with open(pack_dir / "outreach_variants.md", "w", encoding="utf-8") as f:
                                f.write(outreach_md)

                        # 4. Save audit if available
                        if st.session_state.get("audit_result"):
                            status.update(label="Adding audit report...")
                            audit_result = st.session_state["audit_result"]

                            audit_md = f"# Audit Report: {audit_result.domain}\n\n"
                            audit_md += f"**Crawled:** {len(audit_result.crawled_urls)} pages | **Audited:** {len(audit_result.audits)} pages\n\n"

                            for i, audit in enumerate(audit_result.audits, 1):
                                audit_md += f"## Page {i}: {audit.url}\n\n"
                                audit_md += f"**Score:** {audit.score}/100 | **Grade:** {audit.grade}\n\n"
                                audit_md += f"- Content: {audit.content_score}/100\n"
                                audit_md += f"- Technical: {audit.technical_score}/100\n"
                                audit_md += f"- SEO: {audit.seo_score}/100\n\n"

                                if audit.issues:
                                    audit_md += "**Issues:**\n"
                                    for issue in audit.issues:
                                        audit_md += f"- [{issue.severity.upper()}] {issue.description}\n"
                                    audit_md += "\n"

                            if audit_result.quick_wins:
                                audit_md += f"## Top {len(audit_result.quick_wins)} Quick Wins\n\n"
                                for i, task in enumerate(audit_result.quick_wins, 1):
                                    audit_md += f"### {i}. {task.task.title}\n\n"
                                    audit_md += f"**Description:** {task.task.description}\n\n"
                                    audit_md += f"**Impact:** {task.impact:.1f}/10 | **Feasibility:** {task.feasibility:.1f}/10 | **Priority:** {task.priority_score:.1f}/10\n\n"

                            with open(pack_dir / "audit_report.md", "w", encoding="utf-8") as f:
                                f.write(audit_md)

                        # 5. Create ZIP archive
                        status.update(label="Creating ZIP archive...")
                        zip_path = pack_dir.parent / f"{pack_dir.name}.zip"

                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file in pack_dir.glob("*"):
                                if file.is_file():
                                    zipf.write(file, arcname=file.name)

                        status.update(label="✅ Export pack created!", state="complete")
                        st.success(f"✅ Export pack created: {zip_path.name}")
                        st.info(f"**Location:** `{zip_path}`")

                        # Show what's included
                        st.markdown("**Included files:**")
                        for file in pack_dir.glob("*"):
                            st.caption(f"- {file.name}")

                    except Exception as e:
                        st.error(f"Export pack creation failed: {str(e)}")
                        status.update(label="Failed", state="error")

        # Export options
        st.divider()
        st.subheader("Export Classified Leads")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Export to CSV"):
                from pathlib import Path
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                csv_path = out_path / f"classified_leads_{timestamp}.csv"
                filtered_df.to_csv(csv_path, index=False)
                st.success(f"Saved to {csv_path}")

        with col2:
            if st.button("Export to JSON"):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                json_path = out_path / f"classified_leads_{timestamp}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(dataframe_to_json_safe(filtered_df), f, ensure_ascii=False, indent=2)
                st.success(f"Saved to {json_path}")

        with col3:
            if st.button("Export to JSONL"):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                jsonl_path = out_path / f"classified_leads_{timestamp}.jsonl"
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for record in dataframe_to_json_safe(filtered_df):
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                st.success(f"Saved to {jsonl_path}")
    else:
        st.info("👈 Run Hunt first to find leads, then classify them here.")

# ---------------------- OUTREACH TAB ----------------------
with tab3:
    st.subheader("Personalized Outreach Generator")
    st.caption("Generate 3 message variants with deliverability optimization")

    # Check if we have a selected lead
    if st.session_state.get("selected_lead"):
        lead = st.session_state["selected_lead"]
        st.info(f"**Generating outreach for:** {lead.get('name', 'Unknown')} ({lead.get('domain', 'N/A')})")

        col1, col2, col3 = st.columns(3)
        with col1:
            message_type = st.selectbox("Message Type", ["email", "linkedin", "sms"])
        with col2:
            language = st.selectbox("Language", ["en", "fr", "de"])
        with col3:
            tone = st.selectbox("Tone", ["professional", "friendly", "direct"])

        dossier_summary = st.text_area(
            "Dossier Summary (optional)",
            placeholder="Brief company overview from dossier...",
            help="Include key insights from the dossier to personalize the outreach"
        )

        if st.button("Generate Outreach Variants", type="primary"):
            # Progress tracking for variant generation
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            try:
                adapter = get_llm_adapter()

                # Phase 1: Initializing
                status_text.text("🚀 Initializing outreach generation...")
                progress_bar.progress(0.1)

                # Prepare output directory
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "outreach"

                # Phase 2: Generating variants (showing progress for 3 variants)
                status_text.text("✍️ Generating variant 1/3 (Problem-focused)...")
                progress_bar.progress(0.25)

                # Note: compose_outreach generates all 3 at once, so we simulate progress
                import time
                time.sleep(0.5)  # Brief delay to show progress

                status_text.text("✍️ Generating variant 2/3 (Opportunity-focused)...")
                progress_bar.progress(0.5)
                time.sleep(0.5)

                status_text.text("✍️ Generating variant 3/3 (Quick-win focused)...")
                progress_bar.progress(0.75)

                # Generate outreach
                with st.spinner("🤖 LLM generating personalized messages..."):
                    result = compose_outreach(
                        lead_data=lead,
                        llm_adapter=adapter,
                        dossier_summary=dossier_summary if dossier_summary.strip() else None,
                        message_type=message_type,
                        language=language,
                        tone=tone,
                        output_dir=out_path
                    )

                st.session_state["outreach_result"] = result

                # Complete
                progress_bar.progress(1.0)
                status_text.text("✓ Generated 3 outreach variants!")
                st.success(f"✅ Generated {len(result.variants)} personalized {message_type} variants in {language.upper()}")
                st.toast("Outreach variants ready!", icon="✉️")

            except Exception as e:
                st.error(f"Outreach generation failed: {str(e)}")
                status_text.text("❌ Generation failed")

    # Display outreach variants
    if st.session_state.get("outreach_result"):
        result = st.session_state["outreach_result"]

        st.divider()
        st.subheader(f"📧 Outreach Variants ({result.message_type.upper()})")

        for i, variant in enumerate(result.variants, 1):
            with st.expander(f"✉️ Variant {i} - {variant.angle.title()} (Deliverability: {variant.deliverability_score}/100)", expanded=(i==1)):
                # Subject (for email)
                if result.message_type == "email" and variant.subject:
                    st.markdown(f"**Subject:** {variant.subject}")
                    if st.button(f"📋 Copy Subject", key=f"copy_subj_{i}"):
                        st.code(variant.subject, language=None)
                        st.info("Copy the text above to clipboard")

                # Body
                st.markdown("**Message:**")
                st.text_area("", variant.body, height=200, key=f"body_{i}", label_visibility="collapsed")
                if st.button(f"📋 Copy Message", key=f"copy_body_{i}"):
                    st.code(variant.body, language=None)
                    st.info("Copy the text above to clipboard")

                # CTA
                if variant.cta:
                    st.markdown(f"**CTA:** {variant.cta}")

                # Deliverability analysis
                if variant.deliverability_score < 80:
                    st.warning(f"⚠️ Deliverability score: {variant.deliverability_score}/100")
                    if variant.deliverability_issues:
                        st.markdown("**Issues:**")
                        for issue in variant.deliverability_issues:
                            st.caption(f"- {issue}")
                else:
                    st.success(f"✅ Good deliverability: {variant.deliverability_score}/100")

        # Export all variants
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Export All Variants"):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

                # Save as markdown
                md_content = f"# Outreach Variants - {result.company_name}\n\n"
                md_content += f"**Type:** {result.message_type} | **Language:** {result.language} | **Tone:** {result.tone}\n\n"

                for i, variant in enumerate(result.variants, 1):
                    md_content += f"## Variant {i}: {variant.angle.title()}\n\n"
                    if variant.subject:
                        md_content += f"**Subject:** {variant.subject}\n\n"
                    md_content += f"**Message:**\n\n{variant.body}\n\n"
                    if variant.cta:
                        md_content += f"**CTA:** {variant.cta}\n\n"
                    md_content += f"**Deliverability Score:** {variant.deliverability_score}/100\n\n"
                    md_content += "---\n\n"

                md_path = out_path / f"outreach_{result.company_name.replace(' ', '_')}_{timestamp}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                st.success(f"Saved to {md_path}")

        with col2:
            if st.button("📦 Export as JSON"):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

                # Convert to dict
                result_dict = {
                    "company_name": result.company_name,
                    "message_type": result.message_type,
                    "language": result.language,
                    "tone": result.tone,
                    "variants": [
                        {
                            "angle": v.angle,
                            "subject": v.subject,
                            "body": v.body,
                            "cta": v.cta,
                            "deliverability_score": v.deliverability_score,
                            "deliverability_issues": v.deliverability_issues
                        }
                        for v in result.variants
                    ]
                }

                json_path = out_path / f"outreach_{result.company_name.replace(' ', '_')}_{timestamp}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)
                st.success(f"Saved to {json_path}")
    else:
        st.info("👈 Select a lead from the Leads tab first.")

# ---------------------- DOSSIER TAB ----------------------
with tab4:
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

            max_pages_crawl = st.slider("Max pages to crawl", 1, 20, 5)

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
                                timeout=int(s.get("fetch_timeout", 15)),
                                concurrency=int(s.get("concurrency", 8))
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
                        st.success(f"✅ Fetched {len(pages_data)} pages with {sum(len(p.get('content', '')) for p in pages_data)} total characters")
                        st.toast(f"Crawled {len(pages_data)} pages", icon="✅")

                    except Exception as e:
                        st.error(f"Crawl failed: {str(e)}")
                        status_text.text("❌ Crawl failed")
                else:
                    st.warning("Please enter at least one URL")

        else:  # Paste Content
            num_pages = st.number_input("Number of pages", min_value=1, max_value=10, value=2)

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
                    project = s.get("project", "default")
                    out_path = Path(OUT_DIR) / project / "dossiers"

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
                st.markdown("**Social Media:**")
                if dp.social_platforms:
                    for platform in dp.social_platforms:
                        st.caption(f"- {platform}")
                else:
                    st.caption("No social platforms detected")

            if dp.online_reviews:
                st.markdown("**Online Reviews:**")
                st.write(dp.online_reviews)

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
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)

                # Dossier should already be saved by build_dossier
                st.success(f"Dossier saved in {out_path}")

        with col2:
            if st.button("📦 Export as JSON"):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)

                # Dossier should already be saved by build_dossier
                st.success(f"Dossier saved in {out_path}")
    else:
        st.info("👈 Select a lead from the Leads tab and collect pages to analyze.")

# ---------------------- AUDIT TAB ----------------------
with tab5:
    st.subheader("Client Onboarding & Audit")
    st.caption("Run comprehensive site audits and generate prioritized quick wins")

    st.markdown("### Onboarding Mode")
    st.caption("Automated workflow: Crawl → Audit → Quick Wins")

    domain_input = st.text_input("Client Domain", placeholder="https://client-site.com")

    col1, col2 = st.columns(2)
    with col1:
        max_crawl_pages_onboard = st.slider("Max pages to crawl", 5, 50, 10, key="onboard_crawl")
    with col2:
        max_audit_pages_onboard = st.slider("Pages to audit", 1, 10, 3, key="onboard_audit")

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
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "audits"

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
                        concurrency=int(s.get("concurrency", 8))
                    ))

                st.session_state["audit_result"] = result

                progress_bar.progress(1.0)
                status_text.text("✓ Onboarding workflow complete!")
                st.success(f"✅ Audited {len(result.audits)} pages, generated {len(result.quick_wins)} prioritized quick wins")
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

        st.info(f"Crawled: {len(result.crawled_urls)} pages | Audited: {len(result.audits)} pages")

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
        if result.quick_wins:
            st.divider()
            st.subheader(f"⚡ Top Quick Wins ({len(result.quick_wins)})")

            for i, task in enumerate(result.quick_wins, 1):
                with st.expander(f"{i}. {task.task.title} (Priority: {task.priority_score:.1f}/10)", expanded=(i<=3)):
                    st.markdown(f"**Description:** {task.task.description}")
                    st.markdown(f"**Expected Outcome:** {task.task.expected_outcome}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Impact", f"{task.impact:.1f}/10")
                    with col2:
                        st.metric("Feasibility", f"{task.feasibility:.1f}/10")
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
                    st.markdown(f"**Description:** {task.task.description}")
                    st.markdown(f"**Expected Outcome:** {task.task.expected_outcome}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Impact", f"{task.impact:.1f}/10")
                    with col2:
                        st.metric("Feasibility", f"{task.feasibility:.1f}/10")
                    with col3:
                        st.metric("Priority", f"{task.priority_score:.1f}/10")
    else:
        st.info("Enter a domain to run onboarding or a page URL for single audit.")

# ---------------------- SEARCH SCRAPER TAB ----------------------
with tab6:
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
        num_sources = st.slider("Number of sources", 3, 20, 5)
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
            # Create SearchScraper instance with current settings
            scraper = SearchScraper(
                llm_base=s.get("llm_base", ""),
                llm_key=s.get("llm_key", ""),
                llm_model=s.get("llm_model", "gpt-4o-mini"),
                search_engine=s.get("search_engine", "ddg"),
                google_api_key=s.get("google_cse_key", ""),
                google_cx=s.get("google_cse_cx", "")
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
                    timeout=int(s.get("fetch_timeout", 15)),
                    concurrency=int(s.get("concurrency", 8))
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
                    path = os.path.join(OUT_DIR, filename)
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
                    path = os.path.join(OUT_DIR, filename)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"# Query: {result.prompt}\n\n")
                        f.write(f"## Sources\n\n")
                        for source in result.sources:
                            f.write(f"- [{source['url']}]({source['url']})\n")
                        f.write(f"\n\n## Content\n\n{result.markdown_content}")
                    st.success(f"Saved to {path}")

# ---------------------- PLACES TAB ----------------------
with tab7:
    st.subheader("Text search on Google Places")
    st.caption("Requires a valid API key. Uses /places:searchText and detail lookups.")
    query_places = st.text_input("Places text query", placeholder="plombier à Toulouse")
    maxp = st.slider("Max places", 1, 100, 20)
    go_places = st.button("Search Places")
    places_rows = []

    if go_places and query_places:
        key = s.get("google_places_api_key", "")
        if not key:
            st.error("Please set your API key in Settings.")
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            status_text.text("🔍 Searching Google Places...")
            progress_bar.progress(0.1)

            region = s.get("google_places_region", "FR")
            lang = s.get("google_places_language", "fr")
            plist = places_text_search(key, query_places, region=region, language=lang, max_results=maxp) or []

            status_text.text(f"📍 Found {len(plist)} places, fetching details...")
            progress_bar.progress(0.3)

            for i, p in enumerate(plist):
                # Update progress for detail lookups
                if i % 5 == 0 or i == len(plist) - 1:
                    status_text.text(f"📞 Fetching details {i+1}/{len(plist)}...")
                    progress_bar.progress(0.3 + (i / len(plist)) * 0.6)

                pid = p.get("id")
                det = places_details(key, pid, language=lang) if pid else {}
                row = {
                    "name": (p.get("displayName") or {}).get("text"),
                    "address": p.get("formattedAddress"),
                    "website": p.get("websiteUri") or det.get("websiteUri"),
                    "phone": det.get("internationalPhoneNumber"),
                    "place_id": pid
                }
                row["domain"] = domain_of(row["website"] or "") if row["website"] else None
                places_rows.append(row)

            progress_bar.progress(1.0)
            status_text.text(f"✓ Found {len(places_rows)} places")
            st.success(f"✅ Retrieved {len(places_rows)} places with contact details")
            st.toast(f"Found {len(places_rows)} places", icon="📍")

    if places_rows:
        st.dataframe(pd.DataFrame(places_rows), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Export Places CSV"):
                path = export_csv(places_rows)
                exp_placeholder.info(f"Saved CSV at {path}")
        with c2:
            if st.button("Export Places JSON"):
                path = export_json(places_rows)
                exp_placeholder.info(f"Saved JSON at {path}")
        with c3:
            if st.button("Export Places XLSX"):
                path = export_xlsx(places_rows)
                exp_placeholder.info(f"Saved XLSX at {path}")

# ---------------------- REVIEW TAB ----------------------
with tab8:
    st.subheader("Review and edit leads")
    df = pd.DataFrame(st.session_state.get("results", []))
    if not df.empty:
        edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
        csum1, csum2 = st.columns(2)
        with csum1:
            if st.button("Apply changes"):
                st.session_state["results"] = edited.to_dict(orient="records")
                st.success("Updated session results.")
        with csum2:
            if st.button("Summarize with LLM"):
                from llm_client import LLMClient
                cl = LLMClient(
                    api_key=s.get("llm_key", ""),
                    base_url=s.get("llm_base", ""),
                    model=s.get("llm_model", "gpt-4o-mini"),
                    temperature=float(s.get("llm_temperature", 0.2)),
                    max_tokens=int(s.get("llm_max_tokens", 0)) or None
                )
                text = cl.summarize_leads(st.session_state.get("results", []))
                st.text_area("LLM summary", value=text, height=200)
    else:
        st.info("Run Hunt first to get some leads.")

# ---------------------- SEO TOOLS TAB ----------------------
with tab9:
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
                    if use_llm_scoring and s.get("llm_base"):
                        llm_client = LLMClient(
                            api_key=s.get("llm_key", ""),
                            base_url=s.get("llm_base", ""),
                            model=s.get("llm_model", "gpt-4o-mini"),
                            temperature=float(s.get("llm_temperature", 0.2)),
                            max_tokens=int(s.get("llm_max_tokens", 0)) or None
                        )

                    auditor = SEOAuditor(llm_client=llm_client)

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
            serp_results = st.slider("Number of results", 10, 50, 20)

        track_domain = st.text_input("Track specific domain (optional)", placeholder="example.com")

        if st.button("Track SERP", type="primary"):
            if serp_keyword:
                with st.spinner(f"🔍 Tracking SERP positions for '{serp_keyword}'..."):
                    try:
                        tracker = SERPTracker(
                            google_api_key=s.get("google_cse_key", ""),
                            google_cx=s.get("google_cse_cx", "")
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
                                    os.path.join(OUT_DIR, f"serp_{serp_keyword.replace(' ', '_')}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv")
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
            max_sitemap_pages = st.number_input("Max pages", min_value=1, max_value=1000, value=50)

            if st.button("Extract from Sitemap", type="primary"):
                if sitemap_url:
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    try:
                        extractor = SiteExtractor(
                            timeout=int(s.get("fetch_timeout", 15)),
                            concurrency=int(s.get("concurrency", 8))
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
            max_crawl_pages = st.number_input("Max pages to crawl", min_value=1, max_value=200, value=50)
            deep_crawl_site = st.checkbox("Deep crawl (slower, more thorough)", value=True)

            if st.button("Extract from Domain", type="primary"):
                if domain_url:
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    try:
                        extractor = SiteExtractor(
                            timeout=int(s.get("fetch_timeout", 15)),
                            concurrency=int(s.get("concurrency", 8))
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

# ---------------------- SESSION TAB ----------------------
with tab10:
    st.subheader("Session")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    st.write(f"UTC now: {now}")
    st.write(f"Project: {s.get('project', 'default')}")
    st.write(f"Out folder: {OUT_DIR}")
    st.write("Tip: keep rates low and respect robots.txt")
