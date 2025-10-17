"""
Session Tab - Display current session information
"""

import streamlit as st
import datetime


def render_session_tab(settings: dict, out_dir: str):
    """Render the Session tab in the Streamlit UI.

    This function displays information about the current session, such as the current
    time, project name, and output directory.

    Args:
        settings (dict): The current application settings.
        out_dir (str): The path to the output directory.
    """
    st.subheader("Session")

    # Display current UTC time
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    st.write(f"UTC now: {now}")

    # Display project and output folder
    st.write(f"Project: {settings.get('project', 'default')}")
    st.write(f"Out folder: {out_dir}")

    # Display helpful tip
    st.write("Tip: keep rates low and respect robots.txt")
