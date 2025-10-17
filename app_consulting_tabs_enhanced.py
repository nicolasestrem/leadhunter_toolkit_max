# Enhanced Consulting Pack Tabs for app.py
# This file contains the improved UI/UX implementations for tabs 2-5
# Copy and paste these implementations into app.py to replace the current tab implementations

# ===================== ENHANCED LEADS TAB (TAB2) =====================
"""
Replace lines 704-982 in app.py with this enhanced version
"""

def enhanced_leads_tab():
    """Render the enhanced Leads tab in the Streamlit UI.

    This function provides an improved user interface for classifying, scoring,
    and filtering leads.
    """
    st.subheader("Lead Classification & Scoring")
    st.caption("Classify and score leads with multi-dimensional analysis using LLM")

    # Helper function to create LLM adapter
    def get_llm_adapter():
        """Create and return a configured LLM adapter."""
        config_loader = ConfigLoader()
        config = config_loader.get_merged_config()
        return LLMAdapter.from_config(config)

    # Check if we have leads from Hunt tab
    if st.session_state.get("results"):
        st.info(f"📊 Found {len(st.session_state['results'])} leads from Hunt tab. Classify them below.")

        col1, col2 = st.columns([3, 1])
        with col1:
            use_llm_classify = st.checkbox("Use LLM for classification", value=True,
                                          help="Enable LLM to classify business type and detect issues")
        with col2:
            if st.button("🚀 Classify All Leads", type="primary"):
                with st.status("Classifying leads...", expanded=True) as status:
                    try:
                        # Get LLM adapter if enabled
                        adapter = get_llm_adapter() if use_llm_classify else None

                        classified = []
                        for i, lead in enumerate(st.session_state["results"]):
                            status.update(label=f"Classifying lead {i+1}/{len(st.session_state['results'])}...")

                            # Get content sample (combine available text)
                            content_parts = []
                            if lead.get("name"):
                                content_parts.append(f"Company: {lead['name']}")
                            if lead.get("domain"):
                                content_parts.append(f"Domain: {lead['domain']}")
                            if lead.get("notes"):
                                content_parts.append(lead["notes"])
                            content_sample = " ".join(content_parts)

                            # Classify and score
                            lead_record = classify_and_score_lead(
                                lead=lead,
                                llm_adapter=adapter,
                                content_sample=content_sample,
                                use_llm=use_llm_classify
                            )
                            classified.append(lead_record.dict())

                        st.session_state["classified_leads"] = classified
                        status.update(label=f"Classified {len(classified)} leads!", state="complete")
                        st.success(f"✅ Classified {len(classified)} leads")

                    except Exception as e:
                        st.error(f"Classification failed: {str(e)}")
                        status.update(label="Failed", state="error")

    # Display classified leads
    if st.session_state.get("classified_leads"):
        df = pd.DataFrame(st.session_state["classified_leads"])

        # Filters
        st.divider()
        st.subheader("🔍 Filters")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            min_quality = st.slider("Min Quality Score", 0.0, 10.0, 0.0, key="filter_quality")
        with col2:
            min_fit = st.slider("Min Fit Score", 0.0, 10.0, 0.0, key="filter_fit")
        with col3:
            min_priority = st.slider("Min Priority Score", 0.0, 10.0, 0.0, key="filter_priority")
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

        # Display results summary
        st.divider()
        st.subheader(f"📋 Results ({len(filtered_df)} leads)")

        # Select columns to display
        display_cols = ["name", "domain", "score_quality", "score_fit", "score_priority",
                       "business_type", "emails", "phones", "issue_flags", "quality_signals"]
        display_cols = [col for col in display_cols if col in filtered_df.columns]

        st.dataframe(filtered_df[display_cols], use_container_width=True)

        # Lead selection for detailed view
        st.divider()
        st.subheader("🎯 Lead Selector")
        st.caption("Select a lead to view detailed classification and take actions")

        lead_names = [f"{row.get('name', 'Unknown')} ({row.get('domain', 'N/A')})"
                     for _, row in filtered_df.iterrows()]

        if lead_names:
            selected_idx = st.selectbox("Select lead", range(len(lead_names)),
                                       format_func=lambda x: lead_names[x], key="lead_selector")
            selected_lead_data = filtered_df.iloc[selected_idx].to_dict()
            st.session_state["selected_lead"] = selected_lead_data

            # Enhanced lead detail view
            st.divider()
            st.markdown(f"### 🏢 {selected_lead_data.get('name', 'Unknown')}")

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.caption(f"**Domain:** {selected_lead_data.get('domain', 'N/A')}")
            with col2:
                st.caption(f"**Type:** {selected_lead_data.get('business_type', 'Unknown')}")
            with col3:
                if selected_lead_data.get('website'):
                    st.link_button("🌐 Visit", selected_lead_data['website'])

            # Score metrics with visual progress bars and color coding
            st.markdown("#### 📊 Classification Scores")
            col1, col2, col3 = st.columns(3)

            with col1:
                quality_score = selected_lead_data.get('score_quality', 0)
                st.metric("Quality Score", f"{quality_score:.1f}/10")
                # Color coded progress bar
                if quality_score >= 7:
                    st.progress(quality_score / 10.0)
                    st.caption("🟢 Excellent quality")
                elif quality_score >= 5:
                    st.progress(quality_score / 10.0)
                    st.caption("🟡 Good quality")
                else:
                    st.progress(quality_score / 10.0)
                    st.caption("🔴 Needs improvement")

            with col2:
                fit_score = selected_lead_data.get('score_fit', 0)
                st.metric("Fit Score", f"{fit_score:.1f}/10")
                if fit_score >= 7:
                    st.progress(fit_score / 10.0)
                    st.caption("🟢 Strong fit")
                elif fit_score >= 5:
                    st.progress(fit_score / 10.0)
                    st.caption("🟡 Moderate fit")
                else:
                    st.progress(fit_score / 10.0)
                    st.caption("🔴 Weak fit")

            with col3:
                priority_score = selected_lead_data.get('score_priority', 0)
                st.metric("Priority Score", f"{priority_score:.1f}/10")
                if priority_score >= 7:
                    st.progress(priority_score / 10.0)
                    st.caption("🔴 High priority")
                elif priority_score >= 5:
                    st.progress(priority_score / 10.0)
                    st.caption("🟡 Medium priority")
                else:
                    st.progress(priority_score / 10.0)
                    st.caption("🟢 Low priority")

            # Quality signals expandable with better formatting
            if selected_lead_data.get('quality_signals'):
                with st.expander("✅ Quality Signals", expanded=True):
                    signals = selected_lead_data['quality_signals']
                    if isinstance(signals, list):
                        if signals:
                            for signal in signals:
                                st.success(f"• {signal}")
                        else:
                            st.caption("No quality signals detected")
                    else:
                        st.write(signals)

            # Issue flags with severity-based color coding
            if selected_lead_data.get('issue_flags'):
                with st.expander("⚠️ Issue Flags", expanded=True):
                    issues = selected_lead_data['issue_flags']
                    if isinstance(issues, list):
                        if issues:
                            for issue in issues:
                                # Color code issues by severity
                                if any(critical in issue.lower() for critical in ['ssl', 'security', 'malware', 'broken']):
                                    st.error(f"🔴 **CRITICAL:** {issue}")
                                elif any(warning in issue.lower() for warning in ['mobile', 'slow', 'thin', 'seo']):
                                    st.warning(f"🟡 **WARNING:** {issue}")
                                else:
                                    st.info(f"🔵 **INFO:** {issue}")
                        else:
                            st.caption("No issues detected")
                    else:
                        st.write(issues)

            # Contact information with icons and copy buttons
            with st.expander("📇 Contact Information", expanded=False):
                if selected_lead_data.get('emails'):
                    st.markdown("**📧 Emails:**")
                    emails = selected_lead_data['emails'] if isinstance(selected_lead_data['emails'], list) else []
                    for email in emails:
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.caption(f"✉️ {email}")
                        with col_b:
                            if st.button("📋", key=f"copy_email_{email}"):
                                st.code(email, language=None)

                if selected_lead_data.get('phones'):
                    st.markdown("**📞 Phones:**")
                    phones = selected_lead_data['phones'] if isinstance(selected_lead_data['phones'], list) else []
                    for phone in phones:
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.caption(f"☎️ {phone}")
                        with col_b:
                            if st.button("📋", key=f"copy_phone_{phone}"):
                                st.code(phone, language=None)

                if selected_lead_data.get('website'):
                    st.markdown(f"**🌐 Website:** [{selected_lead_data['website']}]({selected_lead_data['website']})")

            # Batch actions
            st.divider()
            st.markdown("### ⚡ Quick Actions")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Re-classify Selected Lead", use_container_width=True):
                    with st.status("Re-classifying lead...", expanded=True) as status:
                        try:
                            adapter = get_llm_adapter() if use_llm_classify else None
                            content_parts = []
                            if selected_lead_data.get("name"):
                                content_parts.append(f"Company: {selected_lead_data['name']}")
                            if selected_lead_data.get("domain"):
                                content_parts.append(f"Domain: {selected_lead_data['domain']}")
                            content_sample = " ".join(content_parts)

                            lead_record = classify_and_score_lead(
                                lead=selected_lead_data,
                                llm_adapter=adapter,
                                content_sample=content_sample,
                                use_llm=use_llm_classify
                            )

                            # Update in classified_leads
                            for i, lead in enumerate(st.session_state["classified_leads"]):
                                if lead.get('domain') == selected_lead_data.get('domain'):
                                    st.session_state["classified_leads"][i] = lead_record.dict()
                                    break

                            status.update(label="Re-classification complete!", state="complete")
                            st.success("✅ Lead re-classified successfully")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Re-classification failed: {str(e)}")
                            status.update(label="Failed", state="error")

            with col2:
                if st.button("📊 View Full Details JSON", use_container_width=True):
                    st.json(selected_lead_data)

            # One-Click Pack Export (keep existing implementation)
            # [... existing pack export code ...]

        # Export options (keep existing)
        # [... existing export code ...]
    else:
        st.info("👈 Run Hunt first to find leads, then classify them here.")


# ===================== ENHANCED OUTREACH TAB (TAB3) =====================
"""
Replace lines 984-1103 in app.py with this enhanced version
"""

def enhanced_outreach_tab():
    """Render the enhanced Outreach tab in the Streamlit UI.

    This function provides an improved user interface for generating personalized
    outreach messages.
    """
    st.subheader("✉️ Personalized Outreach Generator")
    st.caption("Generate 3 message variants with deliverability optimization and vertical-specific templates")

    # Check if we have a selected lead
    if st.session_state.get("selected_lead"):
        lead = st.session_state["selected_lead"]

        # Lead info card
        st.info(f"**📧 Generating outreach for:** {lead.get('name', 'Unknown')} ({lead.get('domain', 'N/A')})")

        # Outreach configuration
        st.markdown("### ⚙️ Configuration")
        col1, col2, col3 = st.columns(3)
        with col1:
            message_type = st.selectbox("📨 Message Type", ["email", "linkedin", "sms"],
                                       help="Choose the communication channel")
        with col2:
            language = st.selectbox("🌍 Language", ["en", "fr", "de"],
                                   help="Select the message language")
        with col3:
            tone = st.selectbox("🎭 Tone", ["professional", "friendly", "direct"],
                               help="Choose the communication tone")

        dossier_summary = st.text_area(
            "📋 Dossier Summary (optional)",
            placeholder="Brief company overview from dossier: Services, pain points, opportunities...",
            help="Include key insights from the dossier to personalize the outreach",
            height=100
        )

        if st.button("🚀 Generate Outreach Variants", type="primary", use_container_width=True):
            with st.status("Generating outreach...", expanded=True) as status:
                try:
                    adapter = get_llm_adapter()

                    status.update(label="Creating personalized variants...")

                    # Prepare output directory
                    project = s.get("project", "default")
                    out_path = Path(OUT_DIR) / project / "outreach"

                    # Generate outreach
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
                    status.update(label="✅ Generated 3 variants!", state="complete")
                    st.success("✅ Outreach variants generated successfully!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Outreach generation failed: {str(e)}")
                    status.update(label="Failed", state="error")

    # Display outreach variants with enhanced UI
    if st.session_state.get("outreach_result"):
        result = st.session_state["outreach_result"]

        st.divider()
        st.subheader(f"📧 Outreach Variants ({result.message_type.upper()})")
        st.caption(f"Language: {result.language.upper()} | Tone: {result.tone.title()}")

        # Display all 3 variants side-by-side in columns
        cols = st.columns(3)

        for i, (col, variant) in enumerate(zip(cols, result.variants), 1):
            with col:
                # Deliverability score with color coding
                deliverability = variant.deliverability_score
                if deliverability >= 90:
                    score_color = "🟢"
                    score_label = "Excellent"
                elif deliverability >= 85:
                    score_color = "🟡"
                    score_label = "Good"
                else:
                    score_color = "🔴"
                    score_label = "Needs Work"

                st.markdown(f"### Variant {i}: {variant.angle.title()}")
                st.caption(f"{score_color} **Deliverability:** {deliverability}/100 ({score_label})")

                # Subject (for email)
                if result.message_type == "email" and variant.subject:
                    st.markdown("**📬 Subject:**")
                    st.text_input("", variant.subject, key=f"subj_{i}", label_visibility="collapsed")
                    if st.button("📋 Copy Subject", key=f"copy_subj_{i}", use_container_width=True):
                        st.code(variant.subject, language=None)
                        st.caption("👆 Copy this to clipboard")

                # Body
                st.markdown("**✉️ Message:**")
                st.text_area("", variant.body, height=250, key=f"body_{i}", label_visibility="collapsed")
                if st.button("📋 Copy Message", key=f"copy_body_{i}", use_container_width=True):
                    st.code(variant.body, language=None)
                    st.caption("👆 Copy this to clipboard")

                # CTA
                if variant.cta:
                    st.markdown(f"**🎯 CTA:** {variant.cta}")

                # Deliverability details in expander
                with st.expander("📊 Deliverability Analysis"):
                    if deliverability < 85:
                        st.warning(f"⚠️ Score: {deliverability}/100")
                        if variant.deliverability_issues:
                            st.markdown("**Issues:**")
                            for issue in variant.deliverability_issues:
                                st.caption(f"• {issue}")
                    else:
                        st.success(f"✅ Score: {deliverability}/100")
                        st.caption("This message has good deliverability!")

        # Export all variants
        st.divider()
        st.markdown("### 💾 Export Options")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 Export All as Markdown", use_container_width=True):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

                # Save as markdown
                md_content = f"# Outreach Variants - {result.company_name}\n\n"
                md_content += f"**Type:** {result.message_type} | **Language:** {result.language} | **Tone:** {result.tone}\n\n"
                md_content += "---\n\n"

                for i, variant in enumerate(result.variants, 1):
                    md_content += f"## Variant {i}: {variant.angle.title()}\n\n"
                    md_content += f"**Deliverability Score:** {variant.deliverability_score}/100\n\n"
                    if variant.subject:
                        md_content += f"**Subject:** {variant.subject}\n\n"
                    md_content += f"**Message:**\n\n{variant.body}\n\n"
                    if variant.cta:
                        md_content += f"**CTA:** {variant.cta}\n\n"
                    md_content += "---\n\n"

                md_path = out_path / f"outreach_{result.company_name.replace(' ', '_')}_{timestamp}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                st.success(f"✅ Saved to {md_path}")

        with col2:
            if st.button("📦 Export as JSON", use_container_width=True):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "outreach"
                out_path.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

                # Convert to dict
                result_dict = {
                    "company_name": result.company_name,
                    "message_type": result.message_type,
                    "language": result.language,
                    "tone": result.tone,
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

                json_path = out_path / f"outreach_{result.company_name.replace(' ', '_')}_{timestamp}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)
                st.success(f"✅ Saved to {json_path}")
    else:
        st.info("👈 Select a lead from the Leads tab first to generate outreach.")


# ===================== ENHANCED DOSSIER TAB (TAB4) =====================
"""
Replace lines 1104-1328 in app.py with this enhanced version
"""

def enhanced_dossier_tab():
    """Render the enhanced Dossier tab in the Streamlit UI.

    This function provides an improved user interface for building and displaying
    client dossiers.
    """
    st.subheader("📋 Client Dossier Builder")
    st.caption("Generate comprehensive RAG-based client dossiers with cited sources and quick wins")

    # Check if we have a selected lead
    if st.session_state.get("selected_lead"):
        lead = st.session_state["selected_lead"]
        st.info(f"**Building dossier for:** {lead.get('name', 'Unknown')} ({lead.get('domain', 'N/A')})")

        # Input for pages to analyze
        st.markdown("### 📄 Pages to Analyze")
        st.caption("Provide URLs or paste page content to include in the dossier")

        page_input_mode = st.radio("Input Mode", ["URLs (will crawl)", "Paste Content"])

        pages_data = []

        if page_input_mode == "URLs (will crawl)":
            urls_input = st.text_area(
                "URLs (one per line)",
                placeholder=f"{lead.get('website', 'https://example.com')}\n{lead.get('website', 'https://example.com')}/about\n{lead.get('website', 'https://example.com')}/services",
                height=150
            )

            max_pages_crawl = st.slider("Max pages to crawl", 1, 20, 5)

            if st.button("🕷️ Crawl Pages", type="primary"):
                if urls_input.strip():
                    with st.status("Crawling pages...", expanded=True) as status:
                        try:
                            urls = [u.strip() for u in urls_input.splitlines() if u.strip().startswith("http")]
                            status.update(label=f"Crawling {len(urls)} URLs...")

                            # Fetch pages
                            pages_dict = asyncio.run(fetch_many(
                                urls,
                                timeout=int(s.get("fetch_timeout", 15)),
                                concurrency=int(s.get("concurrency", 8))
                            ))

                            # Convert to pages data format
                            for url, html in pages_dict.items():
                                if html:
                                    content = text_content(html)
                                    pages_data.append({"url": url, "content": content})

                            st.session_state["dossier_pages"] = pages_data
                            status.update(label=f"✅ Crawled {len(pages_data)} pages", state="complete")
                            st.success(f"✅ Fetched {len(pages_data)} pages")

                        except Exception as e:
                            st.error(f"Crawl failed: {str(e)}")
                            status.update(label="Failed", state="error")
                else:
                    st.warning("Please enter at least one URL")

        else:  # Paste Content
            num_pages = st.number_input("Number of pages", min_value=1, max_value=10, value=2)

            for i in range(num_pages):
                with st.expander(f"Page {i+1}", expanded=(i==0)):
                    url = st.text_input(f"URL {i+1}", key=f"dossier_url_{i}",
                                       value=lead.get('website', '') if i == 0 else '')
                    content = st.text_area(f"Content {i+1}", key=f"dossier_content_{i}",
                                          height=100, placeholder="Paste page content here...")

                    if url and content.strip():
                        # Check if already added
                        existing = next((p for p in pages_data if p['url'] == url), None)
                        if existing:
                            existing['content'] = content
                        else:
                            pages_data.append({"url": url, "content": content})

            if st.button("💾 Save Pages"):
                st.session_state["dossier_pages"] = pages_data
                st.success(f"Saved {len(pages_data)} pages")

        # Show collected pages
        if st.session_state.get("dossier_pages"):
            st.divider()
            st.markdown(f"### 📚 Collected Pages ({len(st.session_state['dossier_pages'])})")

            for i, page in enumerate(st.session_state["dossier_pages"], 1):
                st.caption(f"{i}. {page['url']} ({len(page.get('content', ''))} chars)")

            # Generate dossier
            if st.button("🚀 Generate Dossier", type="primary", use_container_width=True):
                with st.status("Building dossier...", expanded=True) as status:
                    try:
                        adapter = get_llm_adapter()

                        status.update(label="Analyzing pages and generating dossier...")

                        # Prepare output directory
                        project = s.get("project", "default")
                        out_path = Path(OUT_DIR) / project / "dossiers"

                        # Build dossier
                        dossier = build_dossier(
                            lead_data=lead,
                            pages=st.session_state["dossier_pages"],
                            llm_adapter=adapter,
                            output_dir=out_path
                        )

                        st.session_state["dossier_result"] = dossier
                        status.update(label="✅ Dossier generated!", state="complete")
                        st.success("✅ Client dossier generated successfully!")
                        st.balloons()

                    except Exception as e:
                        st.error(f"Dossier generation failed: {str(e)}")
                        status.update(label="Failed", state="error")

    # Display dossier with tabbed organization
    if st.session_state.get("dossier_result"):
        dossier = st.session_state["dossier_result"]

        st.divider()
        st.subheader(f"📊 Dossier: {dossier.company_name}")
        st.caption(f"🌐 {dossier.website} | 📄 {dossier.pages_analyzed} pages analyzed")

        # Tabbed interface for dossier sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Overview",
            "🌐 Digital Presence",
            "💡 Opportunities",
            "👥 Signals",
            "🔍 Issues"
        ])

        with tab1:
            st.markdown("### 🏢 Company Overview")
            st.markdown(dossier.company_overview)

            st.divider()
            st.markdown("### 🛍️ Services & Products")
            if dossier.services_products:
                for i, item in enumerate(dossier.services_products, 1):
                    st.markdown(f"{i}. {item}")
            else:
                st.caption("No services/products identified")

        with tab2:
            st.markdown("### 🌐 Digital Presence Analysis")

            dp = dossier.digital_presence

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🖥️ Website Quality")
                st.info(dp.website_quality or "Not analyzed")

            with col2:
                st.markdown("#### 📱 Social Media")
                if dp.social_platforms:
                    for platform in dp.social_platforms:
                        st.caption(f"✓ {platform}")
                else:
                    st.caption("No social platforms detected")

            if dp.online_reviews:
                st.divider()
                st.markdown("#### ⭐ Online Reviews")
                st.write(dp.online_reviews)

        with tab3:
            st.markdown("### ⚡ 48-Hour Quick Wins")

            if dossier.quick_wins:
                for i, qw in enumerate(dossier.quick_wins, 1):
                    with st.expander(f"**{i}. {qw.title}**", expanded=(i==1)):
                        st.markdown(f"**🎯 Action:** {qw.action}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💥 Impact", qw.impact)
                        with col2:
                            st.metric("⚡ Effort", qw.effort)
                        with col3:
                            priority = qw.priority
                            if priority >= 7:
                                st.metric("🔴 Priority", f"{priority:.1f}/10")
                            elif priority >= 5:
                                st.metric("🟡 Priority", f"{priority:.1f}/10")
                            else:
                                st.metric("🟢 Priority", f"{priority:.1f}/10")
            else:
                st.info("No quick wins identified")

        with tab4:
            st.markdown("### 📡 Signals Detection")

            signals = dossier.signals

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### ✅ Positive Signals")
                if signals.positive:
                    for sig in signals.positive:
                        st.success(f"• {sig}")
                else:
                    st.caption("No positive signals")

            with col2:
                st.markdown("#### 📈 Growth Signals")
                if signals.growth:
                    for sig in signals.growth:
                        st.info(f"• {sig}")
                else:
                    st.caption("No growth signals")

            with col3:
                st.markdown("#### ⚠️ Pain Signals")
                if signals.pain:
                    for sig in signals.pain:
                        st.warning(f"• {sig}")
                else:
                    st.caption("No pain signals")

        with tab5:
            st.markdown("### 🔍 Issues Detected")

            if dossier.issues:
                # Group issues by severity
                critical = [i for i in dossier.issues if i.severity.lower() == "high"]
                warnings = [i for i in dossier.issues if i.severity.lower() == "medium"]
                info = [i for i in dossier.issues if i.severity.lower() == "low"]

                if critical:
                    st.markdown("#### 🔴 Critical Issues")
                    for issue in critical:
                        with st.expander(f"**{issue.category}**"):
                            st.error(issue.description)
                            st.caption(f"Source: {issue.source}")

                if warnings:
                    st.markdown("#### 🟡 Warnings")
                    for issue in warnings:
                        with st.expander(f"**{issue.category}**"):
                            st.warning(issue.description)
                            st.caption(f"Source: {issue.source}")

                if info:
                    st.markdown("#### 🔵 Info")
                    for issue in info:
                        with st.expander(f"**{issue.category}**"):
                            st.info(issue.description)
                            st.caption(f"Source: {issue.source}")
            else:
                st.success("No issues detected!")

        # Sources in footer
        with st.expander(f"📚 Sources ({len(dossier.sources)})", expanded=False):
            for i, source in enumerate(dossier.sources, 1):
                st.markdown(f"{i}. [{source}]({source})")

        # Export options
        st.divider()
        st.markdown("### 💾 Export Options")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 Export as Markdown", use_container_width=True):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)
                st.success(f"✅ Dossier saved in {out_path}")

        with col2:
            if st.button("📦 Export as JSON", use_container_width=True):
                project = s.get("project", "default")
                out_path = Path(OUT_DIR) / project / "dossiers"
                out_path.mkdir(parents=True, exist_ok=True)
                st.success(f"✅ Dossier saved in {out_path}")
    else:
        st.info("👈 Select a lead from the Leads tab and collect pages to analyze.")


# ===================== ENHANCED AUDIT TAB (TAB5) =====================
"""
Replace lines 1330-1534 in app.py with this enhanced version
"""

def enhanced_audit_tab():
    """Render the enhanced Audit tab in the Streamlit UI.

    This function provides an improved user interface for the client onboarding
    wizard and the site audit functionalities.
    """
    st.subheader("🔍 Client Onboarding & Audit")
    st.caption("Run comprehensive site audits and generate prioritized quick wins")

    st.markdown("### 🚀 Onboarding Mode")
    st.caption("Automated workflow: Crawl → Audit → Quick Wins")

    domain_input = st.text_input("🌐 Client Domain", placeholder="https://client-site.com")

    col1, col2 = st.columns(2)
    with col1:
        max_crawl_pages_onboard = st.slider("Max pages to crawl", 5, 50, 10, key="onboard_crawl")
    with col2:
        max_audit_pages_onboard = st.slider("Pages to audit", 1, 10, 3, key="onboard_audit")

    if st.button("🚀 Run Onboarding Wizard", type="primary", use_container_width=True):
        if domain_input:
            with st.status("Running onboarding workflow...", expanded=True) as status:
                try:
                    adapter = get_llm_adapter()

                    status.update(label="Step 1/4: Crawling site...")

                    # Prepare output directory
                    project = s.get("project", "default")
                    out_path = Path(OUT_DIR) / project / "audits"

                    # Run onboarding
                    result = asyncio.run(run_onboarding(
                        domain=domain_input,
                        llm_adapter=adapter,
                        max_crawl_pages=max_crawl_pages_onboard,
                        max_audit_pages=max_audit_pages_onboard,
                        output_dir=out_path,
                        concurrency=int(s.get("concurrency", 8))
                    ))

                    st.session_state["audit_result"] = result
                    status.update(label="✅ Onboarding complete!", state="complete")
                    st.success("✅ Client onboarding completed successfully!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Onboarding failed: {str(e)}")
                    status.update(label="Failed", state="error")
        else:
            st.warning("Please enter a domain")

    # Display onboarding results with enhanced UI
    if st.session_state.get("audit_result"):
        result = st.session_state["audit_result"]

        st.divider()
        st.subheader(f"📊 Audit Results: {result.domain}")

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🕷️ Crawled Pages", len(result.crawled_urls))
        with col2:
            st.metric("📄 Audited Pages", len(result.audits))
        with col3:
            avg_score = sum(a.score for a in result.audits) / len(result.audits) if result.audits else 0
            st.metric("📊 Average Score", f"{avg_score:.0f}/100")

        # Page audits in expandable cards
        st.divider()
        st.markdown("### 📄 Page Audits")

        for i, audit in enumerate(result.audits, 1):
            # Color code grade
            grade_color = {
                "A": "🟢",
                "B": "🟢",
                "C": "🟡",
                "D": "🟡",
                "F": "🔴"
            }.get(audit.grade, "⚪")

            with st.expander(f"{grade_color} **Page {i}:** {audit.url} (Score: {audit.score}/100, Grade: {audit.grade})", expanded=(i==1)):
                # Score metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overall", f"{audit.score}/100")
                with col2:
                    st.metric("Content", f"{audit.content_score}/100")
                with col3:
                    st.metric("Technical", f"{audit.technical_score}/100")
                with col4:
                    st.metric("SEO", f"{audit.seo_score}/100")

                # Issues by severity with cards
                if audit.issues:
                    st.divider()
                    st.markdown("**⚠️ Issues:**")

                    # Group by severity
                    critical = [i for i in audit.issues if i.severity == "critical"]
                    warnings = [i for i in audit.issues if i.severity == "warning"]
                    info_issues = [i for i in audit.issues if i.severity == "info"]

                    if critical:
                        st.markdown("**🔴 Critical:**")
                        for issue in critical:
                            st.error(f"• {issue.description}")

                    if warnings:
                        st.markdown("**🟡 Warnings:**")
                        for issue in warnings:
                            st.warning(f"• {issue.description}")

                    if info_issues:
                        st.markdown("**🔵 Info:**")
                        for issue in info_issues:
                            st.info(f"• {issue.description}")

                # Strengths
                if audit.strengths:
                    st.divider()
                    st.markdown("**✅ Strengths:**")
                    for strength in audit.strengths:
                        st.success(f"• {strength}")

        # Quick wins section with priority cards
        if result.quick_wins:
            st.divider()
            st.subheader(f"⚡ Top Quick Wins ({len(result.quick_wins)})")
            st.caption("Prioritized actions for immediate impact")

            # Group quick wins by priority
            high_priority = [q for q in result.quick_wins if q.priority_score >= 7]
            medium_priority = [q for q in result.quick_wins if 5 <= q.priority_score < 7]
            low_priority = [q for q in result.quick_wins if q.priority_score < 5]

            if high_priority:
                st.markdown("#### 🔴 High Priority")
                for i, task in enumerate(high_priority, 1):
                    with st.expander(f"**{i}. {task.task.title}** (Priority: {task.priority_score:.1f}/10)", expanded=(i<=2)):
                        st.markdown(f"**📝 Action:** {task.task.action}")
                        st.markdown(f"**🎯 Expected Impact:** {task.task.impact}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💥 Impact", f"{task.impact:.1f}/10")
                        with col2:
                            st.metric("⚡ Feasibility", f"{task.feasibility:.1f}/10")
                        with col3:
                            st.metric("🎯 Priority", f"{task.priority_score:.1f}/10")

                        if st.button(f"✅ Mark as Done", key=f"done_{i}"):
                            st.success("Task marked as completed!")

            if medium_priority:
                st.markdown("#### 🟡 Medium Priority")
                for i, task in enumerate(medium_priority, 1):
                    with st.expander(f"**{i}. {task.task.title}** (Priority: {task.priority_score:.1f}/10)"):
                        st.markdown(f"**📝 Action:** {task.task.action}")
                        st.markdown(f"**🎯 Expected Impact:** {task.task.impact}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💥 Impact", f"{task.impact:.1f}/10")
                        with col2:
                            st.metric("⚡ Feasibility", f"{task.feasibility:.1f}/10")
                        with col3:
                            st.metric("🎯 Priority", f"{task.priority_score:.1f}/10")

            if low_priority:
                st.markdown("#### 🟢 Low Priority")
                for i, task in enumerate(low_priority, 1):
                    with st.expander(f"**{i}. {task.task.title}** (Priority: {task.priority_score:.1f}/10)"):
                        st.markdown(f"**📝 Action:** {task.task.action}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("💥 Impact", f"{task.impact:.1f}/10")
                        with col2:
                            st.metric("⚡ Feasibility", f"{task.feasibility:.1f}/10")
                        with col3:
                            st.metric("🎯 Priority", f"{task.priority_score:.1f}/10")

    else:
        st.info("Enter a domain above to run the onboarding wizard and generate a comprehensive audit.")


# ===================== INTEGRATION NOTES =====================
"""
To integrate these enhanced tabs into app.py:

1. Replace the LEADS TAB section (lines 704-982) with enhanced_leads_tab()
2. Replace the OUTREACH TAB section (lines 984-1103) with enhanced_outreach_tab()
3. Replace the DOSSIER TAB section (lines 1104-1328) with enhanced_dossier_tab()
4. Replace the AUDIT TAB section (lines 1330-1534) with enhanced_audit_tab()

Key enhancements:
- Better visual organization with cards, columns, and expandable sections
- Color-coded scores and badges for quick scanning
- Progress bars for visual score representation
- Side-by-side comparison for outreach variants
- Tabbed interface for dossier sections
- Priority-based grouping for audit quick wins
- Enhanced copy-to-clipboard functionality
- Better mobile-friendly layouts
- More descriptive tooltips and captions
- Improved error handling and user feedback
"""
