"""
Enhanced export sidebar section for Lead Hunter Toolkit
Provides filtering, multiple formats, preview, and download buttons
"""

import streamlit as st
import pandas as pd
import os
from export_advanced import (
    ExportFilter, export_filtered_csv, export_filtered_json,
    export_filtered_xlsx, export_filtered_markdown, get_export_preview
)


def render_export_sidebar(project: str):
    """
    Render the advanced export section in the sidebar
    Args:
        project: Current project name from settings
    """
    st.divider()
    st.subheader("Advanced Export")
    st.caption("Export with filtering, multiple formats, and consulting pack")

    # Check if we have leads to export
    has_leads = bool(st.session_state.get("results") or st.session_state.get("classified_leads"))

    if not has_leads:
        st.info("Run Hunt or classify leads first")
        return

    # Export source selection
    export_source = st.radio(
        "Export data from:",
        ["Hunt Results", "Classified Leads"],
        help="Choose which dataset to export",
        key="export_source"
    )

    # Get the appropriate dataset
    if export_source == "Hunt Results":
        export_leads = st.session_state.get("results", [])
    else:
        export_leads = st.session_state.get("classified_leads", [])

    if not export_leads:
        st.info("No leads found in selected source")
        return

    with st.expander("Export Filters", expanded=False):
        # Score filters
        st.caption("**Score Filters**")
        col1, col2 = st.columns(2)
        with col1:
            filter_min_score = st.slider("Min Score", 0.0, 10.0, 0.0, key="exp_min_score")
        with col2:
            filter_max_score = st.slider("Max Score", 0.0, 10.0, 10.0, key="exp_max_score")

        # Multi-dimensional scores (if available)
        if export_leads and 'score_quality' in export_leads[0]:
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_min_quality = st.slider("Min Quality", 0.0, 10.0, 0.0, key="exp_quality")
            with col2:
                filter_min_fit = st.slider("Min Fit", 0.0, 10.0, 0.0, key="exp_fit")
            with col3:
                filter_min_priority = st.slider("Min Priority", 0.0, 10.0, 0.0, key="exp_priority")
        else:
            filter_min_quality = filter_min_fit = filter_min_priority = 0.0

        # Business type filter
        if export_leads and 'business_type' in export_leads[0]:
            business_types = list(set(lead.get('business_type') for lead in export_leads if lead.get('business_type')))
            filter_business_types = st.multiselect("Business Types", business_types, key="exp_business_types")
        else:
            filter_business_types = None

        # Tags filter
        all_tags = set()
        for lead in export_leads:
            all_tags.update(lead.get('tags') or [])
        if all_tags:
            filter_tags = st.multiselect("Tags (any match)", sorted(all_tags), key="exp_tags")
        else:
            filter_tags = None

        # Status filter
        all_statuses = list(set(lead.get('status') for lead in export_leads if lead.get('status')))
        filter_statuses = st.multiselect("Status", all_statuses, default=all_statuses, key="exp_statuses")

        # Contact filters
        col1, col2 = st.columns(2)
        with col1:
            filter_has_emails = st.checkbox("Has emails", value=False, key="exp_has_emails")
        with col2:
            filter_has_phones = st.checkbox("Has phones", value=False, key="exp_has_phones")

        # Column selection
        st.caption("**Column Selection**")
        all_columns = sorted({k for lead in export_leads for k in lead.keys()})

        filter_columns = st.multiselect(
            "Select columns to export (empty = all)",
            all_columns,
            default=None,
            key="exp_columns",
            help="Leave empty to export all columns"
        )

    # Preview button
    if st.button("Preview Export", use_container_width=True):
        # Build filter
        export_filter = ExportFilter(
            min_score=filter_min_score,
            max_score=filter_max_score,
            min_quality=filter_min_quality,
            min_fit=filter_min_fit,
            min_priority=filter_min_priority,
            business_types=filter_business_types if filter_business_types else None,
            tags=filter_tags if filter_tags else None,
            statuses=filter_statuses if filter_statuses else None,
            has_emails=filter_has_emails if filter_has_emails else None,
            has_phones=filter_has_phones if filter_has_phones else None,
            columns=filter_columns if filter_columns else None
        )

        try:
            preview, stats = get_export_preview(export_leads, export_filter, max_preview=5)
            st.session_state["export_preview"] = preview
            st.session_state["export_stats"] = stats
            st.session_state["export_filter"] = export_filter
        except Exception as e:
            st.error(f"Preview error: {e}")

    # Display preview
    if st.session_state.get("export_preview"):
        preview = st.session_state["export_preview"]
        stats = st.session_state["export_stats"]

        st.divider()
        st.caption("**Export Preview**")

        # Statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats["total_filtered"])
        with col2:
            st.metric("Avg Score", f"{stats['avg_score']:.1f}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Emails", stats["has_emails"])
        with col2:
            st.metric("Phones", stats["has_phones"])

        # Multi-dimensional scores
        if "avg_quality" in stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"Quality: {stats['avg_quality']:.1f}/10")
            with col2:
                st.caption(f"Fit: {stats.get('avg_fit', 0):.1f}/10")
            with col3:
                st.caption(f"Priority: {stats.get('avg_priority', 0):.1f}/10")

        # Business type distribution
        if "business_type_distribution" in stats:
            st.caption("**Business Types:**")
            for bt, count in stats["business_type_distribution"].items():
                st.caption(f"- {bt}: {count}")

        # Sample records (compact view)
        with st.expander(f"Sample ({len(preview)} shown)", expanded=False):
            st.dataframe(pd.DataFrame(preview), use_container_width=True)

    # Export format selection and buttons
    st.divider()
    export_format = st.selectbox(
        "Export Format",
        ["CSV", "JSON", "XLSX", "Markdown"],
        key="export_format"
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Export Leads", type="primary", use_container_width=True):
            # Build filter
            export_filter = ExportFilter(
                min_score=filter_min_score,
                max_score=filter_max_score,
                min_quality=filter_min_quality,
                min_fit=filter_min_fit,
                min_priority=filter_min_priority,
                business_types=filter_business_types if filter_business_types else None,
                tags=filter_tags if filter_tags else None,
                statuses=filter_statuses if filter_statuses else None,
                has_emails=filter_has_emails if filter_has_emails else None,
                has_phones=filter_has_phones if filter_has_phones else None,
                columns=filter_columns if filter_columns else None
            )

            try:
                with st.spinner("Exporting..."):
                    if export_format == "CSV":
                        path, count = export_filtered_csv(export_leads, export_filter, project)
                    elif export_format == "JSON":
                        path, count = export_filtered_json(export_leads, export_filter, project)
                    elif export_format == "XLSX":
                        path, count = export_filtered_xlsx(export_leads, export_filter, project)
                    elif export_format == "Markdown":
                        path, count = export_filtered_markdown(export_leads, export_filter, project)

                    st.success(f"Exported {count} records")

                    # Read file for download
                    with open(path, "rb") as f:
                        file_data = f.read()

                    st.download_button(
                        label=f"Download {export_format}",
                        data=file_data,
                        file_name=os.path.basename(path),
                        mime={
                            "CSV": "text/csv",
                            "JSON": "application/json",
                            "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "Markdown": "text/markdown"
                        }[export_format],
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Export failed: {e}")

    with col2:
        # Quick export all (no filters)
        if st.button("Export All", use_container_width=True):
            try:
                with st.spinner("Exporting..."):
                    path, count = export_filtered_csv(
                        export_leads,
                        ExportFilter(),  # No filters
                        project,
                        "leads_all"
                    )
                    st.success(f"Exported {count}")
            except Exception as e:
                st.error(f"Export failed: {e}")
