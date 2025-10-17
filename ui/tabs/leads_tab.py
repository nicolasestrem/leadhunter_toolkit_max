"""
Leads Tab - Lead Classification & Scoring with AI
"""

import streamlit as st
import datetime
import json
import pandas as pd
import zipfile
from pathlib import Path
from config.loader import ConfigLoader
from llm.adapter import LLMAdapter
from leads.classify_score import classify_and_score_lead
from models import Lead
from ui.utils.data_transforms import dict_to_json_safe, dataframe_to_json_safe
from ui.utils.session_state import get_results
from constants import MIN_SCORE, MAX_SCORE, DEFAULT_MIN_QUALITY, DEFAULT_MIN_FIT, DEFAULT_MIN_PRIORITY


def get_llm_adapter():
    """Create and return a configured LLM adapter.

    This helper function abstracts the process of initializing the LLM adapter
    based on the current application configuration.

    Returns:
        LLMAdapter: A configured instance of the LLM adapter.
    """
    config_loader = ConfigLoader()
    config = config_loader.get_merged_config()
    return LLMAdapter.from_config(config)


def render_leads_tab(settings: dict, out_dir: str):
    """Render the Leads tab in the Streamlit UI.

    This function provides the user interface for classifying and scoring leads, as
    well as for filtering and exporting them.

    Args:
        settings (dict): The current application settings.
        out_dir (str): The path to the output directory.
    """
    st.subheader("Lead Classification & Scoring")
    st.caption("Classify and score leads with multi-dimensional analysis using LLM")

    # Check if we have leads from Hunt tab
    if get_results():
        st.info(f"Found {len(get_results())} leads from Hunt tab. Classify them below.")

        col1, col2 = st.columns([3, 1])
        with col1:
            use_llm_classify = st.checkbox("Use LLM for classification", value=True,
                                          help="Enable LLM to classify business type and detect issues")
        with col2:
            if st.button("Classify All Leads", type="primary"):
                # Progress tracking
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                start_time = datetime.datetime.now()

                try:
                    # Get LLM adapter if enabled
                    adapter = get_llm_adapter() if use_llm_classify else None

                    classified = []
                    total_leads = len(get_results())

                    for i, lead in enumerate(get_results()):
                        # Calculate estimated time remaining
                        if i > 0:
                            elapsed = (datetime.datetime.now() - start_time).total_seconds()
                            avg_time_per_lead = elapsed / i
                            remaining_leads = total_leads - i
                            est_remaining = avg_time_per_lead * remaining_leads
                            eta_text = f" (ETA: {int(est_remaining)}s)"
                        else:
                            eta_text = ""

                        status_text.text(f"🔍 Classifying lead {i+1}/{total_leads}: {lead.get('name', 'Unknown')[:40]}...{eta_text}")
                        progress_bar.progress((i + 1) / total_leads)

                        # Get content sample (combine available text)
                        content_parts = []
                        if lead.get("name"):
                            content_parts.append(f"Company: {lead['name']}")
                        if lead.get("domain"):
                            content_parts.append(f"Domain: {lead['domain']}")
                        if lead.get("notes"):
                            content_parts.append(lead["notes"])
                        content_sample = " ".join(content_parts)

                        # Classify and score (convert dict to Lead object)
                        try:
                            lead_obj = Lead(**lead)
                        except Exception as e:
                            st.warning(f"Invalid lead data: {e}")
                            continue

                        lead_record = classify_and_score_lead(
                            lead=lead_obj,
                            llm_adapter=adapter,
                            content_sample=content_sample,
                            use_llm=use_llm_classify
                        )
                        classified.append(lead_record.dict())

                    st.session_state["classified_leads"] = classified

                    # Complete
                    status_text.text(f"✓ Classification complete!")
                    elapsed_total = (datetime.datetime.now() - start_time).total_seconds()
                    avg_time = elapsed_total/len(classified) if classified else 0
                    st.success(f"✅ Classified {len(classified)} leads in {elapsed_total:.1f}s (avg {avg_time:.1f}s per lead)")
                    st.toast(f"Classified {len(classified)} leads", icon="✅")

                except Exception as e:
                    st.error(f"Classification failed: {str(e)}")
                    status_text.text("❌ Classification failed")

    # Display classified leads
    if st.session_state.get("classified_leads"):
        df = pd.DataFrame(st.session_state["classified_leads"])

        # Filters
        st.subheader("Filters")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_quality = st.slider("Min Quality Score", MIN_SCORE, MAX_SCORE, DEFAULT_MIN_QUALITY)
        with col2:
            min_fit = st.slider("Min Fit Score", MIN_SCORE, MAX_SCORE, DEFAULT_MIN_FIT)
        with col3:
            min_priority = st.slider("Min Priority Score", MIN_SCORE, MAX_SCORE, DEFAULT_MIN_PRIORITY)
        with col4:
            business_types = df["business_type"].unique().tolist() if "business_type" in df.columns else []
            selected_types = st.multiselect("Business Type", business_types, default=business_types)

        # Apply filters
        filtered_df = df.copy()
        if "score_quality" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_quality"] >= min_quality]
        if "score_fit" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_fit"] >= min_fit]
        if "score_priority" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["score_priority"] >= min_priority]
        if selected_types and "business_type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["business_type"].isin(selected_types)]

        # Display
        st.subheader(f"Results ({len(filtered_df)} leads)")

        # Select columns to display
        display_cols = ["name", "domain", "score_quality", "score_fit", "score_priority",
                       "business_type", "emails", "phones", "issue_flags", "quality_signals"]
        display_cols = [col for col in display_cols if col in filtered_df.columns]

        st.dataframe(filtered_df[display_cols], use_container_width=True)

        # Lead selection for detailed actions
        st.subheader("Lead Actions")
        lead_names = [f"{row.get('name', 'Unknown')} ({row.get('domain', 'N/A')})"
                     for _, row in filtered_df.iterrows()]

        if lead_names:
            selected_idx = st.selectbox("Select lead for detailed actions", range(len(lead_names)),
                                       format_func=lambda x: lead_names[x])
            st.session_state["selected_lead"] = dict_to_json_safe(filtered_df.iloc[selected_idx].to_dict())

            st.info(f"**Selected:** {lead_names[selected_idx]}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Quality", f"{st.session_state['selected_lead'].get('score_quality', 0):.1f}/10")
            with col2:
                st.metric("Fit", f"{st.session_state['selected_lead'].get('score_fit', 0):.1f}/10")
            with col3:
                st.metric("Priority", f"{st.session_state['selected_lead'].get('score_priority', 0):.1f}/10")

            # One-Click Pack Export
            st.divider()
            st.markdown("### 📦 One-Click Export Pack")
            st.caption("Export complete consulting package: Dossier + Audit + Outreach variants")

            if st.button("📦 Create Export Pack", type="primary", use_container_width=True):
                with st.status("Creating export pack...", expanded=True) as status:
                    try:
                        selected_lead = st.session_state["selected_lead"]
                        project = settings.get("project", "default")
                        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                        company_slug = selected_lead.get('name', 'unknown').replace(' ', '_')

                        # Create pack directory
                        pack_dir = Path(out_dir) / project / f"pack_{company_slug}_{timestamp}"
                        pack_dir.mkdir(parents=True, exist_ok=True)

                        status.update(label="Collecting materials...")

                        # 1. Save lead info
                        with open(pack_dir / "lead_info.json", "w", encoding="utf-8") as f:
                            json.dump(selected_lead, f, ensure_ascii=False, indent=2)

                        # 2. Save dossier if available
                        if st.session_state.get("dossier_result"):
                            status.update(label="Adding dossier...")
                            dossier = st.session_state["dossier_result"]

                            # Markdown
                            dossier_md = f"# Client Dossier: {dossier.company_name}\n\n"
                            dossier_md += f"**Website:** {dossier.website}\n\n"
                            dossier_md += f"## Company Overview\n\n{dossier.company_overview}\n\n"
                            dossier_md += f"## Services & Products\n\n"
                            for item in dossier.services_products:
                                dossier_md += f"- {item}\n"
                            dossier_md += f"\n## Digital Presence\n\n"
                            dossier_md += f"**Website Quality:** {dossier.digital_presence.website_quality}\n\n"
                            if dossier.digital_presence.social_platforms:
                                dossier_md += "**Social Platforms:**\n"
                                for platform in dossier.digital_presence.social_platforms:
                                    dossier_md += f"- {platform}\n"
                            dossier_md += f"\n## Quick Wins\n\n"
                            for i, qw in enumerate(dossier.quick_wins, 1):
                                dossier_md += f"### {i}. {qw.title}\n\n"
                                dossier_md += f"**Action:** {qw.action}\n\n"
                                dossier_md += f"**Impact:** {qw.impact} | **Effort:** {qw.effort} | **Priority:** {qw.priority:.1f}/10\n\n"

                            with open(pack_dir / "dossier.md", "w", encoding="utf-8") as f:
                                f.write(dossier_md)

                        # 3. Save outreach if available
                        if st.session_state.get("outreach_result"):
                            status.update(label="Adding outreach variants...")
                            outreach = st.session_state["outreach_result"]

                            outreach_md = f"# Outreach Variants: {outreach.company_name}\n\n"
                            outreach_md += f"**Type:** {outreach.message_type} | **Language:** {outreach.language} | **Tone:** {outreach.tone}\n\n"

                            for i, variant in enumerate(outreach.variants, 1):
                                outreach_md += f"## Variant {i}: {variant.angle.title()}\n\n"
                                if variant.subject:
                                    outreach_md += f"**Subject:** {variant.subject}\n\n"
                                outreach_md += f"**Message:**\n\n{variant.body}\n\n"
                                if variant.cta:
                                    outreach_md += f"**CTA:** {variant.cta}\n\n"
                                outreach_md += f"**Deliverability:** {variant.deliverability_score}/100\n\n"
                                outreach_md += "---\n\n"

                            with open(pack_dir / "outreach_variants.md", "w", encoding="utf-8") as f:
                                f.write(outreach_md)

                        # 4. Save audit if available
                        if st.session_state.get("audit_result"):
                            status.update(label="Adding audit report...")
                            audit_result = st.session_state["audit_result"]

                            audit_md = f"# Audit Report: {audit_result.domain}\n\n"
                            audit_md += f"**Crawled:** {audit_result.pages_crawled} pages | **Audited:** {audit_result.pages_audited} pages\n\n"

                            for i, audit in enumerate(audit_result.audits, 1):
                                audit_md += f"## Page {i}: {audit.url}\n\n"
                                audit_md += f"**Score:** {audit.score}/100 | **Grade:** {audit.grade}\n\n"
                                audit_md += f"- Content: {audit.content_score}/100\n"
                                audit_md += f"- Technical: {audit.technical_score}/100\n"
                                audit_md += f"- SEO: {audit.seo_score}/100\n\n"

                                if audit.issues:
                                    audit_md += "**Issues:**\n"
                                    for issue in audit.issues:
                                        audit_md += f"- [{issue.severity.upper()}] {issue.description}\n"
                                    audit_md += "\n"

                            if audit_result.all_quick_wins:
                                audit_md += f"## Top {len(audit_result.all_quick_wins)} Quick Wins\n\n"
                                for i, task in enumerate(audit_result.all_quick_wins, 1):
                                    audit_md += f"### {i}. {task.task.title}\n\n"
                                    audit_md += f"**Action:** {task.task.action}\n\n"
                                    audit_md += f"**Impact:** {task.impact:.1f}/10 | **Feasibility:** {task.feasibility:.1f}/10 | **Priority:** {task.priority_score:.1f}/10\n\n"

                            with open(pack_dir / "audit_report.md", "w", encoding="utf-8") as f:
                                f.write(audit_md)

                        # 5. Create ZIP archive
                        status.update(label="Creating ZIP archive...")
                        zip_path = pack_dir.parent / f"{pack_dir.name}.zip"

                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file in pack_dir.glob("*"):
                                if file.is_file():
                                    zipf.write(file, arcname=file.name)

                        status.update(label="✅ Export pack created!", state="complete")
                        st.success(f"✅ Export pack created: {zip_path.name}")
                        st.info(f"**Location:** `{zip_path}`")

                        # Show what's included
                        st.markdown("**Included files:**")
                        for file in pack_dir.glob("*"):
                            st.caption(f"- {file.name}")

                    except Exception as e:
                        st.error(f"Export pack creation failed: {str(e)}")
                        status.update(label="Failed", state="error")

        # Export options
        st.divider()
        st.subheader("Export Classified Leads")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Export to CSV"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                csv_path = out_path / f"classified_leads_{timestamp}.csv"
                filtered_df.to_csv(csv_path, index=False)
                st.success(f"Saved to {csv_path}")

        with col2:
            if st.button("Export to JSON"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                json_path = out_path / f"classified_leads_{timestamp}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(dataframe_to_json_safe(filtered_df), f, ensure_ascii=False, indent=2)
                st.success(f"Saved to {json_path}")

        with col3:
            if st.button("Export to JSONL"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "leads"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
                jsonl_path = out_path / f"classified_leads_{timestamp}.jsonl"
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for record in dataframe_to_json_safe(filtered_df):
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                st.success(f"Saved to {jsonl_path}")
    else:
        st.info("👈 Run Hunt first to find leads, then classify them here.")
