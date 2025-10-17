"""
Page configuration module.
Sets up Streamlit page config and title.
"""
import streamlit as st
from plugins import load_plugins


def setup_page():
    """Configure the Streamlit page and initialize the plugins.

    This function sets the page title and layout, and it ensures that plugins are
    loaded only once during the first run of the application.
    """
    st.set_page_config(
        page_title="Lead Hunter Toolkit • Consulting Pack v1",
        layout="wide"
    )
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

    st.caption(
        "Complete SMB consulting solution: Lead generation, AI-powered classification, "
        "personalized outreach, client dossiers, and comprehensive site audits."
    )
