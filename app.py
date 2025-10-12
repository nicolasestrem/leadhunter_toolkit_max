import streamlit as st
import asyncio, json, os, datetime, pandas as pd
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

st.set_page_config(page_title="Lead Hunter Toolkit • Max", layout="wide")
st.title("Lead Hunter Toolkit • Max")
st.caption("Deeper crawl, presets, classifiers, XLSX export, editable grid, project workspaces, and local LLM helpers.")

# ---- Top docs expander (flat indentation) ----
with st.expander("It worked! What else can I do with this?", expanded=True):
    st.markdown("""
    **SearchScraper** is an advanced LLM powered search that aggregates information from multiple web sources and returns either AI extracted answers with sources or raw markdown content.
    **Modes**
    - AI Extraction Mode default uses AI to extract and structure specific information 10 credits per page
    - Markdown Mode returns raw markdown content from scraped pages 2 credits per page
    """)
    t1, t2, t3 = st.tabs(["Python", "JavaScript", "cURL"])
    with t1:
        st.code("""
from scrapegraph_js import searchScraper

api_key = "your-api-key"
prompt = "What is the latest version of Python and what are its main features?"
num_results = 5
resp = searchScraper(api_key, prompt, num_results)  # AI extraction mode
print(resp)
        """, language="python")
        st.caption("Markdown mode fewer credits set extraction_mode=False")
        st.code("""
from scrapegraph_js import searchScraper

api_key = "your-api-key"
prompt = "Latest developments in artificial intelligence"
resp = searchScraper(api_key, prompt, 3, extraction_mode=False)
print(resp["markdown_content"])
        """, language="python")
    with t2:
        st.code("""
import { searchScraper } from 'scrapegraph-js';

const apiKey = 'your-api-key';
const prompt = 'What is the latest version of Python and what are its main features?';
const numResults = 5;

const response = await searchScraper(apiKey, prompt, numResults);
console.log(response);
        """, language="javascript")
    with t3:
        st.code("""
curl -X POST https://api.scrapegraph.ai/search \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{ "prompt": "Latest developments in AI", "numResults": 3, "extraction_mode": false }'
        """, language="bash")
    st.markdown("""
    **Parameters**
    - apiKey string required your API key
    - prompt string required your query
    - numResults number optional default 3 range 3 to 20
    - extraction_mode boolean optional defaults to true
    - schema object optional only in AI extraction mode
    - mock boolean optional returns mock data for testing

    **Local LLM**
    You can summarize leads with a local model or any OpenAI compatible endpoint. Set **LLM base URL** and **LLM API key** in the sidebar then use **Summarize with LLM** in Review.
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
            "llm_model": llm_model
        })
        save_settings(s)
        st.success("Saved.")
    st.divider()
    st.subheader("Export current table")
    exp_placeholder = st.empty()

tab1, tab2, tab3, tab4 = st.tabs(["Hunt", "Enrich with Places", "Review & Edit", "Session"])

if "results" not in st.session_state:
    st.session_state["results"] = []

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
            with st.status("Searching...", expanded=False) as status:
                engine = s.get("search_engine", "ddg")
                if engine == "google":
                    key = s.get("google_cse_key", "")
                    cx = s.get("google_cse_cx", "")
                    urls = google_sites(q, max_results=max_sites, api_key=key, cx=cx)
                    if not urls:
                        st.warning("Google selected but no results. Check your CSE key and cx.")
                else:
                    urls = ddg_sites(q, max_results=max_sites)
                status.update(label=f"Found {len(urls)} candidate urls.")

        if url_list.strip():
            pasted = [u.strip() for u in url_list.splitlines() if u.strip().startswith("http")]
            urls.extend(pasted)
            urls = list(dict.fromkeys(urls))

        with st.status("Crawling and extracting...", expanded=False) as status:
            settings = dict(s)
            settings["extract_emails"] = extract_emails
            settings["extract_phones"] = extract_phones
            settings["extract_social"] = extract_social
            settings["city"] = city
            settings["deep_contact"] = deep_contact
            settings["max_pages"] = int(max_pages)

            all_pages = {}
            for u in urls:
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

            status.update(label=f"Fetched {len(all_pages)} pages. Extracting...")

            by_domain = {}
            for page_url, html in all_pages.items():
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

            for dom, lead in by_domain.items():
                lead["score"] = score_lead(lead, settings)
                lead["when"] = datetime.datetime.utcnow().isoformat()
                results.append(lead)

            results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
            st.session_state["results"] = results
            status.update(label="Done.", state="complete")

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

# ---------------------- PLACES TAB ----------------------
with tab2:
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
            with st.status("Querying Google Places...", expanded=False) as status:
                region = s.get("google_places_region", "FR")
                lang = s.get("google_places_language", "fr")
                plist = places_text_search(key, query_places, region=region, language=lang, max_results=maxp) or []
                status.update(label=f"Found {len(plist)} places. Pulling details...")
                for p in plist:
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
                status.update(label="Done.", state="complete")

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
with tab3:
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
                cl = LLMClient(api_key=s.get("llm_key",""), base_url=s.get("llm_base",""), model=s.get("llm_model","gpt-4o-mini"))
                text = cl.summarize_leads(st.session_state.get("results", []))
                st.text_area("LLM summary", value=text, height=200)
    else:
        st.info("Run Hunt first to get some leads.")

# ---------------------- SESSION TAB ----------------------
with tab4:
    st.subheader("Session")
    now = datetime.datetime.utcnow().isoformat()
    st.write(f"UTC now: {now}")
    st.write(f"Project: {s.get('project', 'default')}")
    st.write(f"Out folder: {OUT_DIR}")
    st.write("Tip: keep rates low and respect robots.txt")
