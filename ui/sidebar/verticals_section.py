"""
Verticals section for sidebar.
Handles industry-specific preset selection and configuration.
"""
import streamlit as st
from pathlib import Path
from config.loader import ConfigLoader


def render_verticals_section(settings: dict, save_callback) -> dict:
    """Render the vertical presets selector in the sidebar.

    This function provides the UI for selecting and applying industry-specific
    presets, which can influence scoring and outreach generation.

    Args:
        settings (dict): The current settings dictionary.
        save_callback: The function to call when the settings are saved.

    Returns:
        dict: The updated settings dictionary.
    """
    st.divider()
    st.subheader("Vertical Presets")
    st.caption("Industry-specific scoring and outreach optimization")

    # Get available verticals
    verticals_dir = Path(__file__).parent.parent.parent / "presets" / "verticals"
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
            settings["active_vertical"] = new_vertical
            save_callback(settings)

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
                        st.caption(
                            f"**Focus Areas**: {', '.join(focus_areas[:3])}"
                            f"{'...' if len(focus_areas) > 3 else ''}"
                        )

    return settings
