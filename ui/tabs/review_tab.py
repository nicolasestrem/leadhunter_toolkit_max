"""
Review Tab - Edit and summarize leads
"""

import streamlit as st
import pandas as pd
from ui.utils.session_state import get_results, set_results
from llm_client import LLMClient


def render_review_tab(settings: dict):
    """
    Render the Review and Edit tab

    Args:
        settings: Application settings dict
    """
    st.subheader("Review and edit leads")

    df = pd.DataFrame(get_results())

    if not df.empty:
        # Editable data table
        edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Apply changes"):
                set_results(edited.to_dict(orient="records"))
                st.success("Updated session results.")

        with col2:
            if st.button("Summarize with LLM"):
                # Initialize LLM client with user's configured model
                cl = LLMClient(
                    api_key=settings.get("llm_key", ""),
                    base_url=settings.get("llm_base", ""),
                    model=settings.get("llm_model", "gpt-4o-mini"),  # Respect user's model choice
                    temperature=float(settings.get("llm_temperature", 0.6)),
                    top_p=float(settings.get("llm_top_p", 0.9)),
                    max_tokens=int(settings.get("llm_max_tokens", 2048)) or None
                )

                # Generate summary
                text = cl.summarize_leads(get_results())
                st.text_area("LLM summary", value=text, height=200)
    else:
        st.info("Run Hunt first to get some leads.")
