"""Enhanced sidebar rendering helpers."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, MutableMapping, Type

from httpx import HTTPError
from openai import OpenAIError
import streamlit as st

from constants import (
    DEFAULT_CONCURRENCY,
    DEFAULT_FETCH_TIMEOUT,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TOP_K,
    DEFAULT_LLM_TOP_P,
    DEFAULT_MAX_PAGES,
    DEFAULT_MAX_SITES,
    DEFAULT_RADIUS_KM,
    MAX_CONCURRENCY,
    MAX_FETCH_TIMEOUT,
    MAX_LLM_MAX_TOKENS,
    MAX_LLM_TEMPERATURE,
    MAX_LLM_TOP_K,
    MAX_LLM_TOP_P,
    MAX_MAX_PAGES,
    MAX_MAX_SITES,
    MAX_RADIUS_KM,
    MIN_CONCURRENCY,
    MIN_FETCH_TIMEOUT,
    MIN_LLM_TEMPERATURE,
    MIN_LLM_TOP_P,
    MIN_MAX_PAGES,
    MIN_MAX_SITES,
    MIN_RADIUS_KM,
)
from plugins.loader import is_plugin_enabled, set_plugin_enabled


def render_enhanced_sidebar(
    settings: Mapping[str, Any],
    save_callback: Callable[[MutableMapping[str, Any]], None],
    load_plugins_fn: Callable[[], Iterable[Mapping[str, Any]]],
    config_loader_cls: Type[Any],
    path_cls: Type[Any],
) -> MutableMapping[str, Any]:
    """Render the enhanced sidebar UI and return updated settings."""
    mutable_settings: MutableMapping[str, Any] = dict(settings)

    config_loader = config_loader_cls()
    defaults_config = config_loader.load_defaults() or {}
    default_scoring = defaults_config.get("scoring", {})

    with st.form("settings_form"):
        general_tab, crawl_tab, integrations_tab, llm_tab = st.tabs(
            ["General", "Search & Crawl", "Integrations", "LLM"]
        )

        with general_tab:
            search_engine = st.selectbox(
                "Search engine",
                ["ddg", "google"],
                index=0
                if mutable_settings.get("search_engine", "ddg") == "ddg"
                else 1,
                help="Choose the primary engine used for prospect discovery",
            )

            project = st.text_input(
                "Project name", mutable_settings.get("project", "default")
            )

            location_cols = st.columns(2)
            with location_cols[0]:
                country = st.text_input(
                    "Country code", mutable_settings.get("country", "fr")
                )
                city = st.text_input(
                    "City focus", mutable_settings.get("city", "Toulouse")
                )
            with location_cols[1]:
                language = st.text_input(
                    "Language", mutable_settings.get("language", "fr-FR")
                )
                radius_km = st.number_input(
                    "Radius km",
                    min_value=MIN_RADIUS_KM,
                    max_value=MAX_RADIUS_KM,
                    value=int(
                        mutable_settings.get("radius_km", DEFAULT_RADIUS_KM)
                    ),
                )

        with crawl_tab:
            crawl_cols = st.columns(2)
            with crawl_cols[0]:
                max_sites = st.slider(
                    "Max sites per query",
                    MIN_MAX_SITES,
                    MAX_MAX_SITES,
                    int(mutable_settings.get("max_sites", DEFAULT_MAX_SITES)),
                    help="Upper limit of domains captured for each search query",
                )
                fetch_timeout = st.slider(
                    "Fetch timeout (seconds)",
                    MIN_FETCH_TIMEOUT,
                    MAX_FETCH_TIMEOUT,
                    int(
                        mutable_settings.get(
                            "fetch_timeout", DEFAULT_FETCH_TIMEOUT
                        )
                    ),
                )
                deep_contact = st.toggle(
                    "Deep crawl contact/about pages",
                    value=bool(mutable_settings.get("deep_contact", True)),
                )
            with crawl_cols[1]:
                concurrency = st.slider(
                    "Concurrency",
                    MIN_CONCURRENCY,
                    MAX_CONCURRENCY,
                    int(
                        mutable_settings.get("concurrency", DEFAULT_CONCURRENCY)
                    ),
                    help="Number of parallel requests during crawling",
                )
                max_pages = st.slider(
                    "Max pages per site",
                    MIN_MAX_PAGES,
                    MAX_MAX_PAGES,
                    int(mutable_settings.get("max_pages", DEFAULT_MAX_PAGES)),
                )

            extraction_cols = st.columns(4)
            with extraction_cols[0]:
                extract_emails = st.toggle(
                    "Extract emails",
                    value=bool(mutable_settings.get("extract_emails", True)),
                )
            with extraction_cols[1]:
                extract_phones = st.toggle(
                    "Extract phones",
                    value=bool(mutable_settings.get("extract_phones", True)),
                )
            with extraction_cols[2]:
                extract_social = st.toggle(
                    "Extract social links",
                    value=bool(mutable_settings.get("extract_social", True)),
                )
            with extraction_cols[3]:
                extract_structured = st.toggle(
                    "Parse structured data",
                    value=bool(mutable_settings.get("extract_structured", True)),
                    help="Parse schema.org JSON-LD and microdata",
                )

        with integrations_tab:
            st.caption("Manage external services used during prospect discovery.")
            with st.expander(
                "Google Places", expanded=bool(mutable_settings.get("google_places_api_key"))
            ):
                g_api = st.text_input(
                    "API key",
                    value=mutable_settings.get("google_places_api_key", ""),
                    type="password",
                )
                places_cols = st.columns(2)
                with places_cols[0]:
                    g_region = st.text_input(
                        "Places region",
                        value=mutable_settings.get("google_places_region", "FR"),
                    )
                with places_cols[1]:
                    g_lang = st.text_input(
                        "Places language",
                        value=mutable_settings.get("google_places_language", "fr"),
                    )

            with st.expander(
                "Google Custom Search", expanded=bool(mutable_settings.get("google_cse_key"))
            ):
                g_cse_key = st.text_input(
                    "CSE API key",
                    value=mutable_settings.get("google_cse_key", ""),
                    type="password",
                )
                g_cx = st.text_input(
                    "CSE engine ID (cx)",
                    value=mutable_settings.get("google_cse_cx", ""),
                )

        with llm_tab:
            llm_base = st.text_input(
                "LLM base URL (OpenAI compatible)",
                mutable_settings.get("llm_base", ""),
            )
            llm_key = st.text_input(
                "LLM API key",
                value=mutable_settings.get("llm_key", ""),
                type="password",
            )
            llm_model = st.text_input(
                "LLM model", mutable_settings.get("llm_model", "gpt-4o-mini")
            )

            with st.expander("Advanced options"):
                llm_temperature = st.slider(
                    "Temperature",
                    min_value=float(MIN_LLM_TEMPERATURE),
                    max_value=float(MAX_LLM_TEMPERATURE),
                    value=float(
                        mutable_settings.get(
                            "llm_temperature", DEFAULT_LLM_TEMPERATURE
                        )
                    ),
                    step=0.1,
                    help="Controls randomness: 0.0 = deterministic, 2.0 = very creative",
                )
                llm_max_tokens = st.number_input(
                    "Max tokens (0 = unlimited)",
                    min_value=0,
                    max_value=MAX_LLM_MAX_TOKENS,
                    value=int(
                        mutable_settings.get(
                            "llm_max_tokens", DEFAULT_LLM_MAX_TOKENS
                        )
                    ),
                    help="Maximum tokens in LLM response. Important for local models to prevent timeouts.",
                )
                llm_top_k = st.number_input(
                    "Top-K (0 = provider default)",
                    min_value=0,
                    max_value=MAX_LLM_TOP_K,
                    value=int(
                        mutable_settings.get("llm_top_k", DEFAULT_LLM_TOP_K)
                    ),
                    help="Limits vocabulary to the top K tokens. Set to 0 to use provider defaults.",
                )
                llm_top_p = st.slider(
                    "Top-P (nucleus sampling)",
                    min_value=float(MIN_LLM_TOP_P),
                    max_value=float(MAX_LLM_TOP_P),
                    value=float(
                        mutable_settings.get("llm_top_p", DEFAULT_LLM_TOP_P)
                    ),
                    step=0.05,
                    help="Probability mass for nucleus sampling. Lower values focus responses; higher values add creativity.",
                )
                llm_timeout = st.number_input(
                    "LLM timeout (seconds)",
                    min_value=10,
                    max_value=300,
                    value=int(mutable_settings.get("llm_timeout", 60)),
                    help="Maximum time to wait for LLM response",
                )

        save_submit = st.form_submit_button(
            "Save settings", type="primary", use_container_width=True
        )
        test_connection = st.form_submit_button(
            "Test LLM Connection",
            use_container_width=True,
            help="Verify LLM endpoint is accessible",
        )

    if save_submit:
        mutable_settings.update(
            {
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
                "extract_structured": extract_structured,
                "google_places_api_key": g_api,
                "google_places_region": g_region,
                "google_places_language": g_lang,
                "google_cse_key": g_cse_key,
                "google_cse_cx": g_cx,
                "llm_base": llm_base,
                "llm_key": llm_key,
                "llm_model": llm_model,
                "llm_temperature": llm_temperature,
                "llm_max_tokens": llm_max_tokens,
                "llm_top_k": int(llm_top_k),
                "llm_top_p": float(llm_top_p),
                "llm_timeout": llm_timeout,
            }
        )
        save_callback(mutable_settings)
        st.success("Settings saved successfully!")

    if test_connection:
        if llm_base:
            try:
                from llm_client import LLMClient
            except ImportError as exc:
                st.error(f"Unable to load LLM client: {exc}")
            else:
                top_k_param = int(llm_top_k) if int(llm_top_k) > 0 else None
                top_p_param = float(llm_top_p) if llm_top_p else None
                try:
                    with st.spinner("Testing connection..."):
                        test_client = LLMClient(
                            api_key=llm_key or "not-needed",
                            base_url=llm_base,
                            model=llm_model,
                            temperature=0.1,
                            top_k=top_k_param,
                            top_p=top_p_param,
                            max_tokens=50,
                        )
                        response = test_client.chat(
                            [{"role": "user", "content": "Reply with OK"}]
                        )
                        if response:
                            st.success("LLM connection successful!")
                        else:
                            st.error("LLM returned empty response")
                except (
                    OpenAIError,
                    HTTPError,
                    TimeoutError,
                    AttributeError,
                    ValueError,
                    RuntimeError,
                    ConnectionError,
                ) as exc:
                    st.error(f"Connection failed: {exc}")
        else:
            st.warning("Please enter LLM base URL first")

    st.divider()
    st.subheader("🎯 Vertical Presets")
    st.caption("Industry-specific scoring and outreach optimization")

    verticals_dir = path_cls(__file__).parent / "presets" / "verticals"
    available_verticals: list[str] = []
    vertical_icons = {
        "restaurant": "🍽️",
        "retail": "🛍️",
        "professional_services": "💼",
    }

    if verticals_dir.exists():
        available_verticals = [f.stem for f in verticals_dir.glob("*.yml")]

    active_vertical = config_loader.get_active_vertical()

    if active_vertical:
        icon = vertical_icons.get(active_vertical, "📊")
        st.info(f"{icon} **Active**: {active_vertical.replace('_', ' ').title()}")
    else:
        st.caption("⚙️ No vertical preset active (using default settings)")

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_vertical = st.selectbox(
            "Select vertical",
            ["None"] + available_verticals,
            index=0
            if not active_vertical
            else (
                available_verticals.index(active_vertical) + 1
                if active_vertical in available_verticals
                else 0
            ),
            help="Apply industry-specific scoring weights and outreach templates",
            format_func=lambda x: (
                f"{vertical_icons.get(x, '📊')} {x.replace('_', ' ').title()}"
                if x != "None"
                else "⚙️ Default Settings"
            ),
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("Apply", key="apply_vertical", type="primary"):
            new_vertical = None if selected_vertical == "None" else selected_vertical
            mutable_settings["active_vertical"] = new_vertical
            save_callback(mutable_settings)

            config_loader.reload()

            if new_vertical:
                st.success(f"Applied vertical: {new_vertical}")
                st.toast("⚠️ Re-score leads to apply new weights", icon="🔄")
            else:
                st.success("Cleared vertical preset")
            st.rerun()

    if active_vertical and active_vertical in available_verticals:
        vertical_config = config_loader.load_vertical_preset(active_vertical)
        if vertical_config:
            icon = vertical_icons.get(active_vertical, "📊")
            with st.expander(
                f"{icon} {active_vertical.replace('_', ' ').title()} Settings",
                expanded=False,
            ):
                st.markdown(
                    f"**Description:** {vertical_config.get('description', 'N/A')}"
                )

                scoring = vertical_config.get("scoring", {})
                if scoring:
                    st.markdown("**📊 Scoring Weight Adjustments:**")
                    col1, col2, col3 = st.columns(3)

                    weight_keys = list(scoring.keys())
                    for idx, key in enumerate(weight_keys):
                        value = scoring[key]
                        default_val = default_scoring.get(key, 0.0)
                        diff = value - default_val
                        diff_pct = (diff / default_val * 100) if default_val > 0 else 0

                        column = [col1, col2, col3][idx % 3]
                        with column:
                            label = (
                                key.replace("_weight", "").replace("_", " ").title()
                            )
                            if diff > 0:
                                st.metric(
                                    label,
                                    f"{value:.1f}",
                                    f"+{diff_pct:.0f}%",
                                    delta_color="normal",
                                )
                            elif diff < 0:
                                st.metric(
                                    label,
                                    f"{value:.1f}",
                                    f"{diff_pct:.0f}%",
                                    delta_color="inverse",
                                )
                            else:
                                st.metric(
                                    label,
                                    f"{value:.1f}",
                                    "No change",
                                    delta_color="off",
                                )

                outreach = vertical_config.get("outreach", {})
                if outreach:
                    focus_areas = outreach.get("focus_areas", [])
                    if focus_areas:
                        st.markdown("**🎯 Focus Areas:**")
                        for area in focus_areas[:5]:
                            st.caption(f"✓ {area}")
                        if len(focus_areas) > 5:
                            st.caption(f"...and {len(focus_areas) - 5} more")

                    typical_issues = outreach.get("typical_issues", [])
                    if typical_issues:
                        st.markdown("**⚠️ Common Issues to Address:**")
                        for issue in typical_issues[:3]:
                            st.caption(f"• {issue}")

                    value_props = outreach.get("value_props", [])
                    if value_props:
                        st.markdown("**💰 Value Propositions:**")
                        for prop in value_props[:3]:
                            st.caption(f"• {prop}")

                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "🔄 Reset to Defaults", use_container_width=True
                    ):
                        mutable_settings["active_vertical"] = None
                        save_callback(mutable_settings)
                        config_loader.reload()
                        st.success("Reset to default settings")
                        st.rerun()
                with col2:
                    if st.button(
                        "📊 Score Preview",
                        use_container_width=True,
                        help="Preview how scoring changes affect leads",
                    ):
                        st.info(
                            "💡 Apply vertical and re-score leads in the Leads tab to see changes"
                        )

    st.divider()
    st.subheader("🔌 Plugins")
    st.caption("Extend functionality with custom plugins")

    loaded_plugins = st.session_state.get("plugins")
    if loaded_plugins is None:
        try:
            loaded_plugins = list(load_plugins_fn())
            st.session_state.plugins = list(loaded_plugins)
            st.session_state.plugins_loaded = True
        except (RuntimeError, OSError, ImportError) as exc:
            st.error(f"Error loading plugins: {exc}")
            loaded_plugins = []
            st.session_state.plugins = []
            st.session_state.plugins_loaded = False

    if loaded_plugins:
        enabled_count = sum(
            1
            for plugin in loaded_plugins
            if is_plugin_enabled(plugin.get("name", ""))
        )
        st.success(f"✓ {enabled_count} plugin(s) enabled")

        plugin_state = st.session_state.setdefault("plugin_enabled", {})

        for plugin in loaded_plugins:
            plugin_name = plugin.get("name", "Unknown")
            current_enabled = is_plugin_enabled(plugin_name)
            plugin_state.setdefault(plugin_name, current_enabled)

            with st.expander(
                f"🔧 {plugin_name} v{plugin.get('version', '0.0.0')}", expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f"**{plugin.get('description', 'No description')}**"
                    )
                with col2:
                    enabled = st.toggle(
                        "Enable",
                        value=plugin_state[plugin_name],
                        key=f"plugin_toggle_{plugin_name}",
                    )
                    if enabled != plugin_state[plugin_name]:
                        plugin_state[plugin_name] = enabled
                        set_plugin_enabled(plugin_name, enabled)
                    elif current_enabled != plugin_state[plugin_name]:
                        plugin_state[plugin_name] = current_enabled

                if "author" in plugin:
                    st.caption(f"👤 Author: {plugin['author']}")

                hooks = plugin.get("hooks", {})
                if hooks:
                    st.markdown("**🔗 Hook Points:**")
                    for hook_name in hooks.keys():
                        st.caption(f"• `{hook_name}`")

                if plugin_state[plugin_name]:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Status", "✅ Active", delta="Ready")
                    with col2:
                        plugin_path = plugin.get("path", "Unknown")
                        if plugin_path:
                            st.caption(f"📁 {path_cls(plugin_path).name}")
                else:
                    st.warning("⏸️ Plugin disabled")

                if st.button(
                    f"⚙️ Configure",
                    key=f"config_{plugin_name}",
                    disabled=True,
                    use_container_width=True,
                ):
                    st.info("Plugin configuration coming soon")
    else:
        st.caption("No plugins loaded")
        st.info("💡 Add .py files to the plugins/ directory to extend functionality")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🔄 Reload Plugins",
            help="Reload all plugins from plugins/ directory",
            use_container_width=True,
        ):
            if st.session_state.get("confirm_reload_plugins", False):
                try:
                    st.session_state.plugins = list(load_plugins_fn())
                    st.session_state.plugins_loaded = True
                    st.session_state.confirm_reload_plugins = False
                    st.success(
                        f"✅ Reloaded {len(st.session_state.plugins)} plugins"
                    )
                    st.rerun()
                except (RuntimeError, OSError, ImportError) as exc:
                    st.error(f"Error reloading plugins: {exc}")
            else:
                st.session_state.confirm_reload_plugins = True
                st.warning("⚠️ Click again to confirm reload")
    with col2:
        if st.button(
            "ℹ️ Plugin Docs",
            help="View plugin development documentation",
            use_container_width=True,
        ):
            st.info("📚 See plugins/README.md for plugin development guide")

    return mutable_settings

