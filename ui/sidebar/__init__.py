"""
Sidebar orchestrator module.
Coordinates all sidebar sections and returns settings.
"""
import streamlit as st
from .settings_section import render_settings_section
from .verticals_section import render_verticals_section
from .plugins_section import render_plugins_section
from .presets_section import render_presets_section
from .cache_section import render_cache_section


def render_sidebar(settings: dict, save_callback, load_preset_callback) -> dict:
    """Render the complete sidebar with all its sections.

    This function acts as an orchestrator for the sidebar, calling the rendering
    functions for each of its distinct sections.

    Args:
        settings (dict): The current settings dictionary.
        save_callback: The function to call to save settings.
        load_preset_callback: The function to call to load preset data.

    Returns:
        dict: The updated settings dictionary.
    """
    with st.sidebar:
        # Core settings form
        settings = render_settings_section(settings, save_callback)

        # Verticals presets
        settings = render_verticals_section(settings, save_callback)

        # Plugins management
        render_plugins_section()

        # Presets save/load/delete
        settings = render_presets_section(
            settings,
            load_preset_callback,
            save_callback
        )

        # Cache management
        render_cache_section()

        # Export section (imported from external module)
        st.divider()
        from export_sidebar import render_export_sidebar
        render_export_sidebar(settings.get("project", "default"))

        # Placeholder for expansions
        st.empty()

    return settings
