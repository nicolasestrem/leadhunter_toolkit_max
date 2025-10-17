"""
Settings section for sidebar.
Handles core application settings form.
"""
import streamlit as st
from constants import (
    MIN_RADIUS_KM, MAX_RADIUS_KM, DEFAULT_RADIUS_KM,
    MIN_MAX_SITES, MAX_MAX_SITES, DEFAULT_MAX_SITES,
    MIN_FETCH_TIMEOUT, MAX_FETCH_TIMEOUT, DEFAULT_FETCH_TIMEOUT,
    MIN_CONCURRENCY, MAX_CONCURRENCY, DEFAULT_CONCURRENCY,
    MIN_MAX_PAGES, MAX_MAX_PAGES, DEFAULT_MAX_PAGES,
    MIN_LLM_TEMPERATURE, MAX_LLM_TEMPERATURE, DEFAULT_LLM_TEMPERATURE,
    MIN_LLM_TOP_K, MAX_LLM_TOP_K, DEFAULT_LLM_TOP_K,
    MIN_LLM_TOP_P, MAX_LLM_TOP_P, DEFAULT_LLM_TOP_P
)


def render_settings_section(settings: dict, save_callback) -> dict:
    """Render the core application settings form in the sidebar.

    This function creates the user interface for all the main application settings,
    including search, project, crawl, and LLM configurations.

    Args:
        settings (dict): The current settings dictionary.
        save_callback: The function to call when the settings are saved.

    Returns:
        dict: The updated settings dictionary, which is modified when the user saves.
    """
    st.header("Settings")

    # Search and project settings
    search_engine = st.selectbox(
        "Search engine",
        ["ddg", "google"],
        index=0 if settings.get("search_engine", "ddg") == "ddg" else 1
    )

    project = st.text_input("Project name", settings.get("project", "default"))
    country = st.text_input("Country code", settings.get("country", "fr"))
    language = st.text_input("Language", settings.get("language", "fr-FR"))
    city = st.text_input("City focus", settings.get("city", "Toulouse"))
    radius_km = st.number_input(
        "Radius km",
        min_value=MIN_RADIUS_KM,
        max_value=MAX_RADIUS_KM,
        value=int(settings.get("radius_km", DEFAULT_RADIUS_KM))
    )

    # Crawl settings
    max_sites = st.slider(
        "Max sites to scan (per query)",
        MIN_MAX_SITES,
        MAX_MAX_SITES,
        int(settings.get("max_sites", DEFAULT_MAX_SITES))
    )
    fetch_timeout = st.slider(
        "Fetch timeout seconds",
        MIN_FETCH_TIMEOUT,
        MAX_FETCH_TIMEOUT,
        int(settings.get("fetch_timeout", DEFAULT_FETCH_TIMEOUT))
    )
    concurrency = st.slider(
        "Concurrency",
        MIN_CONCURRENCY,
        MAX_CONCURRENCY,
        int(settings.get("concurrency", DEFAULT_CONCURRENCY))
    )
    deep_contact = st.checkbox(
        "Deep crawl contact/about pages",
        value=bool(settings.get("deep_contact", True))
    )
    max_pages = st.slider(
        "Max pages per site",
        MIN_MAX_PAGES,
        MAX_MAX_PAGES,
        int(settings.get("max_pages", DEFAULT_MAX_PAGES))
    )

    # Extraction toggles
    extract_emails = st.checkbox(
        "Extract emails",
        value=bool(settings.get("extract_emails", True))
    )
    extract_phones = st.checkbox(
        "Extract phones",
        value=bool(settings.get("extract_phones", True))
    )
    extract_social = st.checkbox(
        "Extract social links",
        value=bool(settings.get("extract_social", True))
    )

    # Google Places settings
    g_api = st.text_input(
        "Google Places API key",
        value=settings.get("google_places_api_key", ""),
        type="password"
    )
    g_region = st.text_input(
        "Places region",
        value=settings.get("google_places_region", "FR")
    )
    g_lang = st.text_input(
        "Places language",
        value=settings.get("google_places_language", "fr")
    )

    # Google CSE settings
    g_cse_key = st.text_input(
        "Google CSE API key",
        value=settings.get("google_cse_key", ""),
        type="password"
    )
    g_cx = st.text_input(
        "Google CSE cx (engine id)",
        value=settings.get("google_cse_cx", "")
    )

    # LLM settings
    st.subheader("LLM")
    llm_base = st.text_input(
        "LLM base URL (OpenAI compatible)",
        settings.get("llm_base", "")
    )
    llm_key = st.text_input(
        "LLM API key",
        value=settings.get("llm_key", ""),
        type="password"
    )
    llm_model = st.text_input(
        "LLM model",
        settings.get("llm_model", "gpt-4o-mini")
    )

    # Advanced LLM settings
    with st.expander("Advanced LLM Settings"):
        llm_temperature = st.slider(
            "Temperature",
            min_value=MIN_LLM_TEMPERATURE,
            max_value=MAX_LLM_TEMPERATURE,
            value=float(settings.get("llm_temperature", DEFAULT_LLM_TEMPERATURE)),
            step=0.1,
            help="Controls randomness: 0.0 = deterministic, 2.0 = very creative"
        )
        llm_top_k = st.slider(
            "Top-K (LM Studio only - not sent via API)",
            min_value=MIN_LLM_TOP_K,
            max_value=MAX_LLM_TOP_K,
            value=int(settings.get("llm_top_k", DEFAULT_LLM_TOP_K)),
            step=1,
            help="⚠️ REFERENCE ONLY: Configure top_k directly in LM Studio model settings. OpenAI-compatible APIs don't support this parameter via API calls. Recommended: 30 for small_model, 40 for large_model."
        )
        llm_top_p = st.slider(
            "Top-P (Nucleus Sampling)",
            min_value=MIN_LLM_TOP_P,
            max_value=MAX_LLM_TOP_P,
            value=float(settings.get("llm_top_p", DEFAULT_LLM_TOP_P)),
            step=0.05,
            help="Cumulative probability threshold. 0.9 = consider tokens with 90% cumulative prob. Typical range: 0.8-0.95"
        )
        llm_max_tokens = st.number_input(
            "Max tokens (0 = unlimited)",
            min_value=0,
            max_value=128000,
            value=int(settings.get("llm_max_tokens", 0)),
            help="Maximum tokens in LLM response. Important for local models to prevent timeouts."
        )

    # Save button
    if st.button("Save settings"):
        updated_settings = {
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
            "llm_top_k": llm_top_k,
            "llm_top_p": llm_top_p,
            "llm_max_tokens": llm_max_tokens
        }
        settings.update(updated_settings)
        save_callback(settings)
        st.success("Saved.")

    return settings
