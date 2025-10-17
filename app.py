"""
Lead Hunter Toolkit - Main Application
Thin orchestrator that coordinates UI modules
"""

import streamlit as st
import json
import os
from pathlib import Path

# Constants and paths
from constants import BASE_DIR, PRESETS_DIR

SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
OUT_DIR = os.path.join(BASE_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)

# UI modules
from ui.layouts import setup_page, render_quick_start
from ui.sidebar import render_sidebar
from ui.tabs import (
    render_hunt_tab,
    render_leads_tab,
    render_outreach_tab,
    render_dossier_tab,
    render_audit_tab,
    render_search_scraper_tab,
    render_places_tab,
    render_review_tab,
    render_seo_tools_tab,
    render_session_tab
)

# DEFAULT_KEYWORDS for classification (used by tabs)
DEFAULT_KEYWORDS = {
    "plumbing": ["plombier", "plomberie", "plumbing"],
    "restaurant": ["restaurant", "bistrot", "bistro", "cuisine"],
    "seo": ["seo", "référencement", "search engine"],
    "mobility": ["mobilité", "mobility", "transport", "vélo"]
}


# ============================================================================
# Settings Management
# ============================================================================

def load_settings():
    """Load settings from the 'settings.json' file.

    This function reads the content of 'settings.json' and parses it as a JSON object.
    It is designed to handle cases where the file might not exist or is empty by returning
    an empty dictionary.

    Returns:
        dict: A dictionary containing the application settings. Returns an empty dictionary
              if the file cannot be read or does not exist.
    """
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_settings(data: dict):
    """Save the provided settings to the 'settings.json' file.

    This function serializes the given dictionary into a JSON formatted string and
    writes it to 'settings.json', overwriting the file if it already exists. The JSON
    is pretty-printed with an indent of 2 spaces for readability.

    Args:
        data (dict): A dictionary containing the settings to be saved.
    """
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_presets():
    """Scan the presets directory and list all available preset files.

    This function identifies presets by looking for files with a '.json' extension in the
    'PRESETS_DIR'. It extracts the base name of each file (without the extension) to
    represent the preset name.

    Returns:
        list: A sorted list of preset names.
    """
    items = []
    for name in os.listdir(PRESETS_DIR):
        if name.endswith(".json"):
            items.append(name[:-5])
    return sorted(items)


def load_preset(name: str) -> dict:
    """Load a specific preset file by name.

    Constructs the full path to the preset file and loads its JSON content into a
    dictionary. This function is designed to fail gracefully by returning an empty
    dictionary if the file is not found or is invalid.

    Args:
        name (str): The name of the preset to load, without the '.json' extension.

    Returns:
        dict: A dictionary with the preset's content, or an empty dictionary on error.
    """
    path = os.path.join(PRESETS_DIR, name + ".json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_preset(name: str, data: dict):
    """Save a dictionary of settings as a preset file.

    Creates a new preset file or overwrites an existing one. The content of the
    dictionary is serialized to JSON and written to a file named after the preset.

    Args:
        name (str): The name for the preset, which will be used as the filename.
        data (dict): A dictionary containing the settings to be saved in the preset.
    """
    path = os.path.join(PRESETS_DIR, name + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point.

    This function orchestrates the entire Streamlit application. It initializes the page,
    loads settings, renders the user interface components (sidebar and tabs), and
    manages the flow of data between them. Each tab is rendered with the necessary
    settings and configurations.
    """

    # Page configuration and documentation
    setup_page()
    render_quick_start()

    # Load settings
    settings = load_settings()

    # Render sidebar and get updated settings
    settings = render_sidebar(settings, save_settings, load_preset)

    # Tab definitions
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "Hunt", "Leads", "Outreach", "Dossier", "Audit",
        "Search Scraper", "Enrich with Places", "Review & Edit", "SEO Tools", "Session"
    ])

    # Tab routing
    with tab1:
        render_hunt_tab(settings, DEFAULT_KEYWORDS)

    with tab2:
        render_leads_tab(settings, OUT_DIR)

    with tab3:
        render_outreach_tab(settings, OUT_DIR)

    with tab4:
        render_dossier_tab(settings, OUT_DIR)

    with tab5:
        render_audit_tab(settings, OUT_DIR)

    with tab6:
        render_search_scraper_tab(settings, OUT_DIR)

    with tab7:
        render_places_tab(settings)

    with tab8:
        render_review_tab(settings)

    with tab9:
        render_seo_tools_tab(settings, OUT_DIR)

    with tab10:
        render_session_tab(settings, OUT_DIR)


if __name__ == "__main__":
    main()
