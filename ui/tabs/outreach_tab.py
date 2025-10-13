"""
Outreach Tab - Personalized message generation
"""

import streamlit as st
import datetime
import json
import time
from pathlib import Path
from config.loader import ConfigLoader
from llm.adapter import LLMAdapter
from outreach.compose import compose_outreach


def get_llm_adapter():
    """Helper function to create LLM adapter"""
    config_loader = ConfigLoader()
    config = config_loader.get_merged_config()
    return LLMAdapter.from_config(config)


def render_outreach_tab(settings: dict, out_dir: str):
    """
    Render the Outreach tab

    Args:
        settings: Application settings dict
        out_dir: Output directory path
    """
    st.subheader("Personalized Outreach Generator")
    st.caption("Generate 3 message variants with deliverability optimization")

    # Check if we have a selected lead
    if st.session_state.get("selected_lead"):
        lead = st.session_state["selected_lead"]
        st.info(f"**Generating outreach for:** {lead.get('name', 'Unknown')} ({lead.get('domain', 'N/A')})")

        col1, col2, col3 = st.columns(3)
        with col1:
            message_type = st.selectbox("Message Type", ["email", "linkedin", "sms"])
        with col2:
            language = st.selectbox("Language", ["en", "fr", "de"])
        with col3:
            tone = st.selectbox("Tone", ["professional", "friendly", "direct"])

        dossier_summary = st.text_area(
            "Dossier Summary (optional)",
            placeholder="Brief company overview from dossier...",
            help="Include key insights from the dossier to personalize the outreach"
        )

        if st.button("Generate Outreach Variants", type="primary"):
            # Progress tracking for variant generation
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            try:
                adapter = get_llm_adapter()

                # Phase 1: Initializing
                status_text.text("🚀 Initializing outreach generation...")
                progress_bar.progress(0.1)

                # Prepare output directory
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "outreach"

                # Phase 2: Generating variants (showing progress for 3 variants)
                status_text.text("✍️ Generating variant 1/3 (Problem-focused)...")
                progress_bar.progress(0.25)

                # Note: compose_outreach generates all 3 at once, so we simulate progress
                time.sleep(0.5)  # Brief delay to show progress

                status_text.text("✍️ Generating variant 2/3 (Opportunity-focused)...")
                progress_bar.progress(0.5)
                time.sleep(0.5)

                status_text.text("✍️ Generating variant 3/3 (Quick-win focused)...")
                progress_bar.progress(0.75)

                # Generate outreach
                with st.spinner("🤖 LLM generating personalized messages..."):
                    result = compose_outreach(
                        lead_data=lead,
                        llm_adapter=adapter,
                        dossier_summary=dossier_summary if dossier_summary.strip() else None,
                        message_type=message_type,
                        language=language,
                        tone=tone,
                        output_dir=out_path
                    )

                st.session_state["outreach_result"] = result

                # Complete
                progress_bar.progress(1.0)
                status_text.text("✓ Generated 3 outreach variants!")
                st.success(f"✅ Generated {len(result.variants)} personalized {message_type} variants in {language.upper()}")
                st.toast("Outreach variants ready!", icon="✉️")

            except Exception as e:
                st.error(f"Outreach generation failed: {str(e)}")
                status_text.text("❌ Generation failed")

    # Display outreach variants
    if st.session_state.get("outreach_result"):
        result = st.session_state["outreach_result"]

        st.divider()
        st.subheader(f"📧 Outreach Variants ({result.message_type.upper()})")

        for i, variant in enumerate(result.variants, 1):
            with st.expander(f"✉️ Variant {i} - {variant.angle.title()} (Deliverability: {variant.deliverability_score}/100)", expanded=(i==1)):
                # Subject (for email)
                if result.message_type == "email" and variant.subject:
                    st.markdown(f"**Subject:** {variant.subject}")
                    if st.button(f"📋 Copy Subject", key=f"copy_subj_{i}"):
                        st.code(variant.subject, language=None)
                        st.info("Copy the text above to clipboard")

                # Body
                st.markdown("**Message:**")
                st.text_area("Message preview", variant.body, height=200, key=f"body_{i}", label_visibility="collapsed")
                if st.button(f"📋 Copy Message", key=f"copy_body_{i}"):
                    st.code(variant.body, language=None)
                    st.info("Copy the text above to clipboard")

                # CTA
                if variant.cta:
                    st.markdown(f"**CTA:** {variant.cta}")

                # Deliverability analysis
                if variant.deliverability_score < 80:
                    st.warning(f"⚠️ Deliverability score: {variant.deliverability_score}/100")
                    if variant.deliverability_issues:
                        st.markdown("**Issues:**")
                        for issue in variant.deliverability_issues:
                            st.caption(f"- {issue}")
                else:
                    st.success(f"✅ Good deliverability: {variant.deliverability_score}/100")

        # Export all variants
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Export All Variants"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

                # Save as markdown
                md_content = f"# Outreach Variants - {result.lead_name}\n\n"
                md_content += f"**Type:** {result.message_type} | **Language:** {result.language}\n\n"

                for i, variant in enumerate(result.variants, 1):
                    md_content += f"## Variant {i}: {variant.angle.title()}\n\n"
                    if variant.subject:
                        md_content += f"**Subject:** {variant.subject}\n\n"
                    md_content += f"**Message:**\n\n{variant.body}\n\n"
                    if variant.cta:
                        md_content += f"**CTA:** {variant.cta}\n\n"
                    md_content += f"**Deliverability Score:** {variant.deliverability_score}/100\n\n"
                    md_content += "---\n\n"

                md_path = out_path / f"outreach_{result.lead_name.replace(' ', '_')}_{timestamp}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                st.success(f"Saved to {md_path}")

        with col2:
            if st.button("📦 Export as JSON"):
                project = settings.get("project", "default")
                out_path = Path(out_dir) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

                # Convert to dict
                result_dict = {
                    "lead_name": result.lead_name,
                    "message_type": result.message_type,
                    "language": result.language,
                    "variants": [
                        {
                            "angle": v.angle,
                            "subject": v.subject,
                            "body": v.body,
                            "cta": v.cta,
                            "deliverability_score": v.deliverability_score,
                            "deliverability_issues": v.deliverability_issues
                        }
                        for v in result.variants
                    ]
                }

                json_path = out_path / f"outreach_{result.lead_name.replace(' ', '_')}_{timestamp}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)
                st.success(f"Saved to {json_path}")
    else:
        st.info("👈 Select a lead from the Leads tab first.")
