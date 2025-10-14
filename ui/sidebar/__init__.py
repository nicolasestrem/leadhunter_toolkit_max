"""Sidebar orchestrator module."""
from pathlib import Path
from typing import Callable, Dict

import streamlit as st

from config.loader import ConfigLoader
from plugins import load_plugins

from sidebar_enhanced import render_enhanced_sidebar

from .presets_section import render_presets_section
from .cache_section import render_cache_section


def render_sidebar(
    settings: Dict,
    save_callback: Callable[[Dict], None],
    load_preset_callback: Callable[[str], Dict],
) -> Dict:
    """Render complete sidebar with all sections."""
    with st.sidebar:
        settings = render_enhanced_sidebar(
            settings,
            save_callback,
            load_plugins,
            ConfigLoader,
            Path,
        )

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
