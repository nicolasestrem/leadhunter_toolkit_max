"""
Reusable export button components
Provides consistent CSV/JSON/XLSX export UI across all tabs
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from exporters import export_csv, export_json
from exporters_xlsx import export_xlsx


def render_export_buttons(
    data: List[Dict[str, Any]],
    namespace: str = "default",
    show_csv: bool = True,
    show_json: bool = True,
    show_xlsx: bool = True,
    label_prefix: str = "Export"
):
    """
    Render CSV/JSON/XLSX export buttons in a row

    Args:
        data: List of dicts to export
        namespace: Export namespace/prefix for filename
        show_csv: Whether to show CSV export button
        show_json: Whether to show JSON export button
        show_xlsx: Whether to show XLSX export button
        label_prefix: Prefix for button labels (default: "Export")

    Example:
        render_export_buttons(results, namespace="leads")
    """
    if not data:
        st.info("No data to export")
        return

    # Create columns for buttons
    cols = []
    if show_csv:
        cols.append(None)
    if show_json:
        cols.append(None)
    if show_xlsx:
        cols.append(None)

    if len(cols) == 0:
        return

    cols = st.columns(len(cols))
    col_idx = 0

    # CSV Export
    if show_csv:
        with cols[col_idx]:
            if st.button(f"{label_prefix} CSV", use_container_width=True):
                try:
                    path = export_csv(data, namespace)
                    st.success(f"✓ Saved to {path}")
                except Exception as e:
                    st.error(f"Export failed: {e}")
        col_idx += 1

    # JSON Export
    if show_json:
        with cols[col_idx]:
            if st.button(f"{label_prefix} JSON", use_container_width=True):
                try:
                    path = export_json(data, namespace)
                    st.success(f"✓ Saved to {path}")
                except Exception as e:
                    st.error(f"Export failed: {e}")
        col_idx += 1

    # XLSX Export
    if show_xlsx:
        with cols[col_idx]:
            if st.button(f"{label_prefix} XLSX", use_container_width=True):
                try:
                    path = export_xlsx(data, namespace)
                    st.success(f"✓ Saved to {path}")
                except Exception as e:
                    st.error(f"Export failed: {e}")


def render_single_export_button(
    data: List[Dict[str, Any]],
    export_type: str,
    namespace: str = "default",
    label: Optional[str] = None,
    use_container_width: bool = False
):
    """
    Render a single export button

    Args:
        data: Data to export
        export_type: One of "csv", "json", "xlsx"
        namespace: Export namespace
        label: Custom button label (default: "Export {TYPE}")
        use_container_width: Whether button should fill container width
    """
    if not data:
        st.info("No data to export")
        return

    if label is None:
        label = f"Export {export_type.upper()}"

    if st.button(label, use_container_width=use_container_width):
        try:
            if export_type.lower() == "csv":
                path = export_csv(data, namespace)
            elif export_type.lower() == "json":
                path = export_json(data, namespace)
            elif export_type.lower() == "xlsx":
                path = export_xlsx(data, namespace)
            else:
                st.error(f"Unknown export type: {export_type}")
                return

            st.success(f"✓ Saved to {path}")
        except Exception as e:
            st.error(f"Export failed: {e}")
