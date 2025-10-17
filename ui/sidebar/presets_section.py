"""
Presets section for sidebar.
Handles preset save/load/delete functionality.
"""
import os
import streamlit as st
from constants import PRESETS_DIR


def list_presets():
    """Get a list of available preset names.

    This function scans the presets directory for '.json' files and returns a sorted
    list of their base names.

    Returns:
        list: A sorted list of preset names.
    """
    items = []
    for name in os.listdir(PRESETS_DIR):
        if name.endswith(".json"):
            items.append(name[:-5])
    return sorted(items)


def render_presets_section(settings: dict, load_callback, save_callback) -> dict:
    """Render the presets management section in the sidebar.

    This function provides the UI for loading, saving, and deleting configuration presets.

    Args:
        settings (dict): The current settings dictionary.
        load_callback: The function to call to load preset data.
        save_callback: The function to call to save settings.

    Returns:
        dict: The updated settings dictionary, which may be modified if a preset is loaded.
    """
    st.divider()
    st.subheader("Presets")
    st.caption("Save/load configurations per niche or location")

    presets = list_presets()

    # Load preset
    col1, col2 = st.columns(2)
    with col1:
        selected_preset = st.selectbox("Load preset", [""] + presets)
    with col2:
        if selected_preset:
            if st.button("Load"):
                preset_data = load_callback(selected_preset)
                if preset_data:
                    settings.update(preset_data)
                    save_callback(settings)
                    st.success(f"Loaded preset: {selected_preset}")
                    st.rerun()

    # Save preset
    preset_name = st.text_input("Save as preset", placeholder="berlin_plumbers")
    if st.button("Save preset"):
        if preset_name:
            import json
            preset_path = os.path.join(PRESETS_DIR, preset_name + ".json")
            with open(preset_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            st.success(f"Saved preset: {preset_name}")
        else:
            st.warning("Please enter a preset name")

    # Delete preset
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

    return settings
