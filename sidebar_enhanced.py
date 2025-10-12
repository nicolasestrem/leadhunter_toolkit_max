# Enhanced Sidebar Section for app.py
# Replace lines 275-471 in app.py with this code

# ---- Sidebar ----
with st.sidebar:
    st.header("Settings")
    s = load_settings()

    # Load config loader for vertical support
    config_loader = ConfigLoader()

    # Get default scoring weights for comparison
    defaults_config = config_loader.load_defaults()
    default_scoring = defaults_config.get('scoring', {})

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

        # LLM timeout setting
        llm_timeout = st.number_input(
            "LLM timeout (seconds)",
            min_value=10,
            max_value=300,
            value=int(s.get("llm_timeout", 60)),
            help="Maximum time to wait for LLM response"
        )

        # Test connection button
        if st.button("Test LLM Connection", help="Verify LLM endpoint is accessible"):
            if llm_base:
                try:
                    from llm_client import LLMClient
                    with st.spinner("Testing connection..."):
                        test_client = LLMClient(
                            api_key=llm_key or "not-needed",
                            base_url=llm_base,
                            model=llm_model,
                            temperature=0.1,
                            max_tokens=50
                        )
                        # Simple test prompt
                        response = test_client.chat([{"role": "user", "content": "Reply with OK"}])
                        if response:
                            st.success("LLM connection successful!")
                        else:
                            st.error("LLM returned empty response")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
            else:
                st.warning("Please enter LLM base URL first")

    if st.button("Save settings", type="primary", use_container_width=True):
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
            "llm_max_tokens": llm_max_tokens,
            "llm_timeout": llm_timeout
        })
        save_settings(s)
        st.success("Settings saved successfully!")

    st.divider()
    st.subheader("🎯 Vertical Presets")
    st.caption("Industry-specific scoring and outreach optimization")

    # Get available verticals
    verticals_dir = Path(__file__).parent / "presets" / "verticals"
    available_verticals = []
    vertical_icons = {
        "restaurant": "🍽️",
        "retail": "🛍️",
        "professional_services": "💼"
    }

    if verticals_dir.exists():
        available_verticals = [
            f.stem for f in verticals_dir.glob("*.yml")
        ]

    # Get currently active vertical
    active_vertical = config_loader.get_active_vertical()

    # Show current status with icon
    if active_vertical:
        icon = vertical_icons.get(active_vertical, "📊")
        st.info(f"{icon} **Active**: {active_vertical.replace('_', ' ').title()}")
    else:
        st.caption("⚙️ No vertical preset active (using default settings)")

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
            help="Apply industry-specific scoring weights and outreach templates",
            format_func=lambda x: f"{vertical_icons.get(x, '📊')} {x.replace('_', ' ').title()}" if x != "None" else "⚙️ Default Settings"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Apply", key="apply_vertical", type="primary"):
            # Update settings with new vertical
            new_vertical = None if selected_vertical == "None" else selected_vertical
            s["active_vertical"] = new_vertical
            save_settings(s)

            # Reload config to apply changes
            config_loader.reload()

            if new_vertical:
                st.success(f"Applied vertical: {new_vertical}")
                st.toast("⚠️ Re-score leads to apply new weights", icon="🔄")
            else:
                st.success("Cleared vertical preset")
            st.rerun()

    # Show vertical details if active
    if active_vertical and active_vertical in available_verticals:
        vertical_config = config_loader.load_vertical_preset(active_vertical)
        if vertical_config:
            icon = vertical_icons.get(active_vertical, "📊")
            with st.expander(f"{icon} {active_vertical.replace('_', ' ').title()} Settings", expanded=False):
                st.markdown(f"**Description:** {vertical_config.get('description', 'N/A')}")

                # Scoring weight differences
                scoring = vertical_config.get('scoring', {})
                if scoring:
                    st.markdown("**📊 Scoring Weight Adjustments:**")
                    col1, col2, col3 = st.columns(3)

                    weight_keys = list(scoring.keys())
                    for idx, key in enumerate(weight_keys):
                        value = scoring[key]
                        default_val = default_scoring.get(key, 0.0)
                        diff = value - default_val
                        diff_pct = (diff / default_val * 100) if default_val > 0 else 0

                        col = [col1, col2, col3][idx % 3]
                        with col:
                            label = key.replace('_weight', '').replace('_', ' ').title()
                            if diff > 0:
                                st.metric(label, f"{value:.1f}", f"+{diff_pct:.0f}%", delta_color="normal")
                            elif diff < 0:
                                st.metric(label, f"{value:.1f}", f"{diff_pct:.0f}%", delta_color="inverse")
                            else:
                                st.metric(label, f"{value:.1f}", "No change", delta_color="off")

                # Show outreach focus areas
                outreach = vertical_config.get('outreach', {})
                if outreach:
                    focus_areas = outreach.get('focus_areas', [])
                    if focus_areas:
                        st.markdown("**🎯 Focus Areas:**")
                        for area in focus_areas[:5]:
                            st.caption(f"✓ {area}")
                        if len(focus_areas) > 5:
                            st.caption(f"...and {len(focus_areas) - 5} more")

                    # Typical issues
                    typical_issues = outreach.get('typical_issues', [])
                    if typical_issues:
                        st.markdown("**⚠️ Common Issues to Address:**")
                        for issue in typical_issues[:3]:
                            st.caption(f"• {issue}")

                    # Value propositions
                    value_props = outreach.get('value_props', [])
                    if value_props:
                        st.markdown("**💰 Value Propositions:**")
                        for prop in value_props[:3]:
                            st.caption(f"• {prop}")

                # Reset button
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Reset to Defaults", use_container_width=True):
                        s["active_vertical"] = None
                        save_settings(s)
                        config_loader.reload()
                        st.success("Reset to default settings")
                        st.rerun()
                with col2:
                    if st.button("📊 Score Preview", use_container_width=True, help="Preview how scoring changes affect leads"):
                        st.info("💡 Apply vertical and re-score leads in the Leads tab to see changes")

    st.divider()
    st.subheader("🔌 Plugins")
    st.caption("Extend functionality with custom plugins")

    # Get loaded plugins
    loaded_plugins = st.session_state.get('plugins', [])

    if loaded_plugins:
        st.success(f"✓ {len(loaded_plugins)} plugin(s) active")

        # Initialize plugin settings in session state
        if 'plugin_enabled' not in st.session_state:
            st.session_state.plugin_enabled = {p.get('name', ''): True for p in loaded_plugins}

        # Show plugin cards
        for plugin in loaded_plugins:
            plugin_name = plugin.get('name', 'Unknown')

            with st.expander(f"🔧 {plugin_name} v{plugin.get('version', '0.0.0')}", expanded=False):
                # Header with toggle
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{plugin.get('description', 'No description')}**")
                with col2:
                    enabled = st.toggle(
                        "Enable",
                        value=st.session_state.plugin_enabled.get(plugin_name, True),
                        key=f"plugin_toggle_{plugin_name}"
                    )
                    st.session_state.plugin_enabled[plugin_name] = enabled

                # Plugin metadata
                if 'author' in plugin:
                    st.caption(f"👤 Author: {plugin['author']}")

                # Hook points
                hooks = plugin.get('hooks', {})
                if hooks:
                    st.markdown("**🔗 Hook Points:**")
                    for hook_name in hooks.keys():
                        st.caption(f"• `{hook_name}`")

                # Plugin statistics (mock data - can be enhanced)
                if enabled:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Status", "✅ Active", delta="Ready")
                    with col2:
                        # Show file path
                        plugin_path = plugin.get('path', 'Unknown')
                        if plugin_path:
                            st.caption(f"📁 {Path(plugin_path).name}")
                else:
                    st.warning("⏸️ Plugin disabled")

                # Configure button (placeholder for future plugin-specific settings)
                if st.button(f"⚙️ Configure", key=f"config_{plugin_name}", disabled=True, use_container_width=True):
                    st.info("Plugin configuration coming soon")
    else:
        st.caption("No plugins loaded")
        st.info("💡 Add .py files to the plugins/ directory to extend functionality")

    # Reload plugins button with confirmation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reload Plugins", help="Reload all plugins from plugins/ directory", use_container_width=True):
            if st.session_state.get('confirm_reload_plugins', False):
                try:
                    st.session_state.plugins = load_plugins()
                    st.session_state.plugins_loaded = True
                    st.session_state.confirm_reload_plugins = False
                    st.success(f"✅ Reloaded {len(st.session_state.plugins)} plugins")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reloading plugins: {e}")
            else:
                st.session_state.confirm_reload_plugins = True
                st.warning("⚠️ Click again to confirm reload")
    with col2:
        if st.button("ℹ️ Plugin Docs", help="View plugin development documentation", use_container_width=True):
            st.info("📚 See plugins/README.md for plugin development guide")
