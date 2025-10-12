"""
Code Snippets Library for Consulting Pack Tabs Enhancement
============================================================

This file contains reusable code snippets for common UI patterns
used in the enhanced consulting pack tabs. Copy and paste as needed.

Author: Claude Code
Date: 2025-10-12
Version: 1.0
"""

import streamlit as st
import pandas as pd

# ============================================================
# PATTERN 1: Score Display with Progress Bar and Color Coding
# ============================================================

def display_score_with_progress(label: str, score: float, max_score: float = 10.0):
    """
    Display a score with progress bar and color-coded caption.

    Args:
        label: Label for the metric
        score: Current score value
        max_score: Maximum possible score (default 10.0)

    Example:
        display_score_with_progress("Quality Score", 7.5, 10.0)
    """
    st.metric(label, f"{score:.1f}/{max_score:.0f}")
    st.progress(score / max_score)

    # Color-coded feedback
    percentage = (score / max_score) * 100
    if percentage >= 70:
        st.caption("🟢 Excellent")
    elif percentage >= 50:
        st.caption("🟡 Good")
    else:
        st.caption("🔴 Needs improvement")


# ============================================================
# PATTERN 2: Severity-Based Issue Display
# ============================================================

def display_issue_with_severity(issue_text: str, severity: str):
    """
    Display an issue with appropriate color coding based on severity.

    Args:
        issue_text: The issue description
        severity: One of "critical", "warning", "info"

    Example:
        display_issue_with_severity("SSL certificate expired", "critical")
    """
    severity_lower = severity.lower()

    if severity_lower in ["critical", "high", "error"]:
        st.error(f"🔴 **CRITICAL:** {issue_text}")
    elif severity_lower in ["warning", "medium", "warn"]:
        st.warning(f"🟡 **WARNING:** {issue_text}")
    else:
        st.info(f"🔵 **INFO:** {issue_text}")


# ============================================================
# PATTERN 3: Side-by-Side Comparison Layout
# ============================================================

def display_variants_side_by_side(variants: list):
    """
    Display items side-by-side in equal columns.

    Args:
        variants: List of items to display (max 3 recommended)

    Example:
        variants = [
            {"title": "Variant 1", "content": "..."},
            {"title": "Variant 2", "content": "..."},
            {"title": "Variant 3", "content": "..."}
        ]
        display_variants_side_by_side(variants)
    """
    cols = st.columns(len(variants))

    for i, (col, variant) in enumerate(zip(cols, variants), 1):
        with col:
            st.markdown(f"### {variant.get('title', f'Item {i}')}")
            st.write(variant.get('content', ''))


# ============================================================
# PATTERN 4: Deliverability Score Badge
# ============================================================

def display_deliverability_badge(score: int):
    """
    Display a deliverability score with color-coded badge.

    Args:
        score: Deliverability score (0-100)

    Example:
        display_deliverability_badge(92)
    """
    if score >= 90:
        color = "🟢"
        label = "Excellent"
    elif score >= 85:
        color = "🟡"
        label = "Good"
    else:
        color = "🔴"
        label = "Needs Work"

    st.caption(f"{color} **Deliverability:** {score}/100 ({label})")


# ============================================================
# PATTERN 5: Priority-Based Grouping
# ============================================================

def group_items_by_priority(items: list, priority_key: str = "priority"):
    """
    Group items into high/medium/low priority categories.

    Args:
        items: List of items with priority scores
        priority_key: Key name for priority value (default "priority")

    Returns:
        Dict with keys: "high", "medium", "low"

    Example:
        tasks = [
            {"title": "Task 1", "priority": 8.5},
            {"title": "Task 2", "priority": 5.2},
            {"title": "Task 3", "priority": 3.1}
        ]
        grouped = group_items_by_priority(tasks)
    """
    high = [i for i in items if i.get(priority_key, 0) >= 7]
    medium = [i for i in items if 5 <= i.get(priority_key, 0) < 7]
    low = [i for i in items if i.get(priority_key, 0) < 5]

    return {"high": high, "medium": medium, "low": low}


def display_grouped_items(grouped_items: dict):
    """
    Display items grouped by priority with color-coded headers.

    Args:
        grouped_items: Output from group_items_by_priority()

    Example:
        grouped = group_items_by_priority(tasks)
        display_grouped_items(grouped)
    """
    if grouped_items["high"]:
        st.markdown("#### 🔴 High Priority")
        for i, item in enumerate(grouped_items["high"], 1):
            with st.expander(f"**{i}. {item.get('title', 'Untitled')}**", expanded=(i<=2)):
                st.write(item.get('description', ''))

    if grouped_items["medium"]:
        st.markdown("#### 🟡 Medium Priority")
        for i, item in enumerate(grouped_items["medium"], 1):
            with st.expander(f"**{i}. {item.get('title', 'Untitled')}**"):
                st.write(item.get('description', ''))

    if grouped_items["low"]:
        st.markdown("#### 🟢 Low Priority")
        for i, item in enumerate(grouped_items["low"], 1):
            with st.expander(f"**{i}. {item.get('title', 'Untitled')}**"):
                st.write(item.get('description', ''))


# ============================================================
# PATTERN 6: Tabbed Content Organization
# ============================================================

def create_tabbed_dossier(dossier_data: dict):
    """
    Create a tabbed interface for dossier sections.

    Args:
        dossier_data: Dict with keys for each tab's content

    Example:
        dossier = {
            "overview": "Company overview text...",
            "digital": "Digital presence info...",
            "opportunities": [...quick wins...],
            "signals": {...signals...},
            "issues": [...issues...]
        }
        create_tabbed_dossier(dossier)
    """
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview",
        "🌐 Digital Presence",
        "💡 Opportunities",
        "👥 Signals",
        "🔍 Issues"
    ])

    with tab1:
        st.markdown("### 🏢 Company Overview")
        st.write(dossier_data.get("overview", "No overview available"))

    with tab2:
        st.markdown("### 🌐 Digital Presence")
        st.write(dossier_data.get("digital", "No digital presence data"))

    with tab3:
        st.markdown("### 💡 Opportunities")
        opportunities = dossier_data.get("opportunities", [])
        for i, opp in enumerate(opportunities, 1):
            st.markdown(f"{i}. {opp}")

    with tab4:
        st.markdown("### 👥 Signals")
        signals = dossier_data.get("signals", {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Positive**")
            for sig in signals.get("positive", []):
                st.success(f"• {sig}")
        with col2:
            st.markdown("**📈 Growth**")
            for sig in signals.get("growth", []):
                st.info(f"• {sig}")
        with col3:
            st.markdown("**⚠️ Pain**")
            for sig in signals.get("pain", []):
                st.warning(f"• {sig}")

    with tab5:
        st.markdown("### 🔍 Issues")
        issues = dossier_data.get("issues", [])
        for issue in issues:
            display_issue_with_severity(issue.get("description"), issue.get("severity"))


# ============================================================
# PATTERN 7: Copy to Clipboard Button
# ============================================================

def display_with_copy_button(text: str, button_label: str = "📋 Copy", key: str = None):
    """
    Display text with a copy button.

    Args:
        text: Text to display and copy
        button_label: Label for copy button
        key: Unique key for button

    Example:
        display_with_copy_button("john@example.com", "Copy Email", "email_1")
    """
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text_input("", text, key=f"text_{key}", label_visibility="collapsed")
    with col2:
        if st.button(button_label, key=f"btn_{key}"):
            st.code(text, language=None)
            st.caption("👆 Copy to clipboard")


# ============================================================
# PATTERN 8: Enhanced Metric Display
# ============================================================

def display_metrics_grid(metrics: list):
    """
    Display metrics in a responsive grid.

    Args:
        metrics: List of dicts with keys: label, value, delta (optional)

    Example:
        metrics = [
            {"label": "Quality", "value": "7.5/10", "delta": "+0.5"},
            {"label": "Fit", "value": "8.2/10", "delta": "+1.2"},
            {"label": "Priority", "value": "6.8/10"}
        ]
        display_metrics_grid(metrics)
    """
    cols = st.columns(len(metrics))

    for col, metric in zip(cols, metrics):
        with col:
            st.metric(
                metric["label"],
                metric["value"],
                delta=metric.get("delta")
            )


# ============================================================
# PATTERN 9: Collapsible Info Cards
# ============================================================

def display_info_cards(items: list, expanded_first: bool = True):
    """
    Display items as collapsible cards.

    Args:
        items: List of dicts with keys: title, content, icon (optional)
        expanded_first: Whether to expand the first card

    Example:
        cards = [
            {"title": "Overview", "content": "Details...", "icon": "🏢"},
            {"title": "Contact", "content": "Email...", "icon": "📧"}
        ]
        display_info_cards(cards)
    """
    for i, item in enumerate(items):
        icon = item.get("icon", "📋")
        title = item.get("title", "Untitled")
        content = item.get("content", "")

        with st.expander(f"{icon} {title}", expanded=(i == 0 and expanded_first)):
            st.write(content)


# ============================================================
# PATTERN 10: Status Progress Indicator
# ============================================================

def display_status_progress(current_step: int, total_steps: int, step_names: list):
    """
    Display a progress indicator for multi-step processes.

    Args:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps
        step_names: List of step names

    Example:
        display_status_progress(2, 4, ["Crawl", "Extract", "Analyze", "Export"])
    """
    progress = current_step / total_steps
    st.progress(progress)

    status_text = f"Step {current_step}/{total_steps}: {step_names[current_step-1]}"
    st.caption(status_text)


# ============================================================
# PATTERN 11: Filter Controls
# ============================================================

def create_lead_filters():
    """
    Create filter controls for lead classification view.

    Returns:
        Dict with filter values

    Example:
        filters = create_lead_filters()
        # Apply filters to dataframe
        df = df[df['quality'] >= filters['min_quality']]
    """
    st.subheader("🔍 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        min_quality = st.slider("Min Quality Score", 0.0, 10.0, 0.0, key="filter_quality")
    with col2:
        min_fit = st.slider("Min Fit Score", 0.0, 10.0, 0.0, key="filter_fit")
    with col3:
        min_priority = st.slider("Min Priority Score", 0.0, 10.0, 0.0, key="filter_priority")
    with col4:
        business_types = st.multiselect("Business Type", ["restaurant", "retail", "services"], key="filter_types")

    return {
        "min_quality": min_quality,
        "min_fit": min_fit,
        "min_priority": min_priority,
        "business_types": business_types
    }


# ============================================================
# PATTERN 12: Export Buttons Group
# ============================================================

def create_export_buttons(data, filename_base: str):
    """
    Create a group of export buttons (CSV, JSON, XLSX).

    Args:
        data: Data to export (DataFrame or list of dicts)
        filename_base: Base name for export files

    Example:
        create_export_buttons(leads_df, "classified_leads")
    """
    st.divider()
    st.subheader("💾 Export Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export CSV", use_container_width=True):
            # Export logic here
            st.success(f"Exported {filename_base}.csv")

    with col2:
        if st.button("📦 Export JSON", use_container_width=True):
            # Export logic here
            st.success(f"Exported {filename_base}.json")

    with col3:
        if st.button("📊 Export XLSX", use_container_width=True):
            # Export logic here
            st.success(f"Exported {filename_base}.xlsx")


# ============================================================
# PATTERN 13: Enhanced Table Display
# ============================================================

def display_enhanced_table(df: pd.DataFrame, title: str = None):
    """
    Display a DataFrame with enhanced styling and controls.

    Args:
        df: DataFrame to display
        title: Optional title for the table

    Example:
        display_enhanced_table(leads_df, "Classified Leads")
    """
    if title:
        st.subheader(title)

    # Display record count
    st.caption(f"📊 Showing {len(df)} records")

    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# PATTERN 14: Action Card with Buttons
# ============================================================

def display_action_card(title: str, description: str, actions: list):
    """
    Display a card with title, description, and action buttons.

    Args:
        title: Card title
        description: Card description
        actions: List of dicts with keys: label, callback, type (optional)

    Example:
        actions = [
            {"label": "View Details", "callback": lambda: st.write("Details")},
            {"label": "Edit", "callback": lambda: st.write("Edit"), "type": "secondary"}
        ]
        display_action_card("Lead Name", "Company description", actions)
    """
    st.markdown(f"### {title}")
    st.write(description)

    cols = st.columns(len(actions))
    for col, action in zip(cols, actions):
        with col:
            button_type = action.get("type", "primary")
            if st.button(
                action["label"],
                key=f"action_{title}_{action['label']}",
                type=button_type,
                use_container_width=True
            ):
                action["callback"]()


# ============================================================
# PATTERN 15: Loading State Handler
# ============================================================

def with_loading_status(operation_name: str, operation_func, *args, **kwargs):
    """
    Execute a function with loading status display.

    Args:
        operation_name: Name of the operation for status display
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Result of operation_func

    Example:
        result = with_loading_status(
            "Classifying leads",
            classify_leads,
            leads_data
        )
    """
    with st.status(f"{operation_name}...", expanded=True) as status:
        try:
            result = operation_func(*args, **kwargs)
            status.update(label=f"✅ {operation_name} complete!", state="complete")
            st.success(f"✅ {operation_name} completed successfully")
            return result
        except Exception as e:
            status.update(label="Failed", state="error")
            st.error(f"{operation_name} failed: {str(e)}")
            return None


# ============================================================
# USAGE EXAMPLES
# ============================================================

def example_usage():
    """
    Example usage of all patterns.
    Run this to see the patterns in action.
    """
    st.title("Code Snippets Demo")

    # Example 1: Score Display
    st.header("1. Score Display with Progress")
    col1, col2, col3 = st.columns(3)
    with col1:
        display_score_with_progress("Quality", 7.5)
    with col2:
        display_score_with_progress("Fit", 5.2)
    with col3:
        display_score_with_progress("Priority", 3.8)

    # Example 2: Severity Issues
    st.header("2. Severity-Based Issues")
    display_issue_with_severity("SSL certificate expired", "critical")
    display_issue_with_severity("Page load time slow", "warning")
    display_issue_with_severity("Missing alt text", "info")

    # Example 3: Deliverability Badge
    st.header("3. Deliverability Badge")
    display_deliverability_badge(92)

    # Example 4: Priority Grouping
    st.header("4. Priority Grouping")
    tasks = [
        {"title": "Add SSL", "priority": 9.0, "description": "Critical security fix"},
        {"title": "Optimize images", "priority": 6.5, "description": "Improve load time"},
        {"title": "Update footer", "priority": 2.0, "description": "Minor cosmetic change"}
    ]
    grouped = group_items_by_priority(tasks)
    display_grouped_items(grouped)

    # Example 5: Metrics Grid
    st.header("5. Metrics Grid")
    metrics = [
        {"label": "Leads", "value": "42", "delta": "+12"},
        {"label": "Qualified", "value": "18", "delta": "+5"},
        {"label": "Converted", "value": "7", "delta": "+2"}
    ]
    display_metrics_grid(metrics)


# ============================================================
# RUN EXAMPLES
# ============================================================

if __name__ == "__main__":
    # Uncomment to see examples
    # example_usage()
    pass
