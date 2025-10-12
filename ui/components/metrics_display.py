"""
Reusable metric display components
Provides consistent metric cards and score displays across all tabs
"""

import streamlit as st
from typing import List, Tuple, Optional, Dict, Any


def render_score_metrics(
    quality: float,
    fit: float,
    priority: float,
    max_score: float = 10.0
):
    """
    Render three-column score metrics (Quality, Fit, Priority)

    Args:
        quality: Quality score
        fit: Fit score
        priority: Priority score
        max_score: Maximum score value (default: 10.0)

    Example:
        render_score_metrics(8.5, 7.2, 9.1)
    """
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Quality", f"{quality:.1f}/{max_score:.0f}")
    with col2:
        st.metric("Fit", f"{fit:.1f}/{max_score:.0f}")
    with col3:
        st.metric("Priority", f"{priority:.1f}/{max_score:.0f}")


def render_audit_scores(
    overall: int,
    content: int,
    technical: int,
    seo: int,
    max_score: int = 100
):
    """
    Render four-column audit score metrics

    Args:
        overall: Overall score
        content: Content score
        technical: Technical score
        seo: SEO score
        max_score: Maximum score value (default: 100)

    Example:
        render_audit_scores(85, 90, 75, 88)
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Overall", f"{overall}/{max_score}")
    with col2:
        st.metric("Content", f"{content}/{max_score}")
    with col3:
        st.metric("Technical", f"{technical}/{max_score}")
    with col4:
        st.metric("SEO", f"{seo}/{max_score}")


def render_task_metrics(
    impact: float,
    feasibility: float,
    priority: float,
    max_score: float = 10.0
):
    """
    Render three-column task metrics (Impact, Feasibility, Priority)

    Args:
        impact: Impact score
        feasibility: Feasibility score
        priority: Priority score
        max_score: Maximum score value (default: 10.0)

    Example:
        render_task_metrics(8.5, 6.0, 7.8)
    """
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Impact", f"{impact:.1f}/{max_score:.0f}")
    with col2:
        st.metric("Feasibility", f"{feasibility:.1f}/{max_score:.0f}")
    with col3:
        st.metric("Priority", f"{priority:.1f}/{max_score:.0f}")


def render_metrics_row(metrics: List[Tuple[str, str]], num_columns: Optional[int] = None):
    """
    Render a row of metrics with custom labels and values

    Args:
        metrics: List of (label, value) tuples
        num_columns: Number of columns (default: len(metrics))

    Example:
        render_metrics_row([
            ("Cache Files", "42 files"),
            ("Cache Size", "15.3 MB"),
            ("Hit Rate", "87%")
        ])
    """
    if num_columns is None:
        num_columns = len(metrics)

    cols = st.columns(num_columns)

    for idx, (label, value) in enumerate(metrics):
        if idx < len(cols):
            with cols[idx]:
                st.metric(label, value)


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None
):
    """
    Render a single metric card with optional delta

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: Color for delta ("normal", "inverse", "off")
        help_text: Optional help text tooltip

    Example:
        render_metric_card("Score", "8.5/10", delta="+1.2", delta_color="normal")
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def render_kv_table(data: Dict[str, Any], title: Optional[str] = None):
    """
    Render a key-value table using st.write

    Args:
        data: Dictionary of key-value pairs
        title: Optional title for the table

    Example:
        render_kv_table({"Name": "John", "Email": "john@example.com"})
    """
    if title:
        st.subheader(title)

    for key, value in data.items():
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{key}:**")
        with col2:
            st.write(value)
