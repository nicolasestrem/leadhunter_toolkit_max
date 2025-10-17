"""
Documentation module.
Renders quick start guide and help documentation.
"""
import streamlit as st


def render_quick_start():
    """Render the quick start guide in a Streamlit expander.

    This function creates a collapsible section in the UI that contains comprehensive
    documentation for all of the application's features and workflows.
    """
    with st.expander("📚 Quick Start Guide", expanded=False):
        st.markdown("""
    ## Lead Hunter Toolkit • Consulting Pack v1

    ### 🎯 Complete Workflow

    **Step 1: Hunt** → Find leads through web search or paste URLs
    **Step 2: Classify** → Use AI to score leads (quality, fit, priority)
    **Step 3: Generate Outreach** → Create personalized messages in 3 variants
    **Step 4: Build Dossier** → Comprehensive analysis with quick wins
    **Step 5: Audit Site** → Technical SEO audit with recommendations
    **Step 6: Export Pack** → One-click export of all materials

    ---

    ### 🎯 Hunt Tab
    **Lead Generation & Discovery**
    - Search the web (DuckDuckGo or Google Custom Search)
    - Or paste URLs to scan directly
    - Smart BFS crawling with contact/about page prioritization
    - Extract emails, phones, social links automatically
    - Export to CSV, JSON, or XLSX

    ### 📊 Leads Tab (NEW!)
    **AI-Powered Classification & Scoring**
    - Multi-dimensional scoring: Quality, Fit, Priority (0-10)
    - Business type classification (restaurant, retail, services, etc.)
    - Issue flags detection (No SSL, thin content, poor mobile)
    - Quality signals identification
    - Advanced filtering by score and business type
    - Export to CSV, JSON, JSONL

    **Workflow:**
    1. Run Hunt to find leads
    2. Go to Leads tab
    3. Click "Classify All Leads" (uses LLM)
    4. Filter by scores and business type
    5. Select a lead for detailed actions

    ### ✉️ Outreach Tab (NEW!)
    **Personalized Message Generation**
    - Generate 3 message variants (problem, opportunity, quick-win angles)
    - Support for email, LinkedIn, SMS
    - Multilingual: English, French, German
    - Tone presets: Professional, Friendly, Direct
    - Deliverability checking (spam detection, word count, links)
    - Copy-to-clipboard buttons

    **Workflow:**
    1. Select a lead in Leads tab
    2. Go to Outreach tab
    3. Choose message type, language, tone
    4. Add optional dossier summary
    5. Generate 3 variants
    6. Review deliverability scores
    7. Export all variants

    ### 📋 Dossier Tab (NEW!)
    **RAG-Based Client Analysis**
    - Company overview with cited sources
    - Services/products identification
    - Digital presence analysis
    - Signals: Positive, Growth, Pain
    - Issues detected with severity
    - 48-hour quick wins (5 tasks)

    **Workflow:**
    1. Select a lead in Leads tab
    2. Go to Dossier tab
    3. Enter URLs to crawl OR paste content
    4. Generate dossier (uses LLM)
    5. Review all sections
    6. Export as Markdown or JSON

    ### 🔍 Audit Tab (NEW!)
    **Site Audits & Quick Wins**

    **Onboarding Wizard:**
    - Automated: Crawl → Audit → Quick Wins
    - Configurable page limits
    - Prioritized recommendations

    **Single Page Audit:**
    - LLM-enhanced analysis
    - Scores: Overall, Content, Technical, SEO
    - Issues by severity (critical, warning, info)
    - Strengths identification
    - Quick wins generation

    **Workflow:**
    1. Enter client domain
    2. Run Onboarding Wizard
    3. Review page audits and scores
    4. Check top quick wins
    5. Export report

    ### 📦 One-Click Export Pack (NEW!)
    **Complete Consulting Package**
    - Lead info (JSON)
    - Dossier (Markdown)
    - Outreach variants (Markdown)
    - Audit report (Markdown)
    - All packaged in a ZIP file

    **Workflow:**
    1. Complete Leads, Outreach, Dossier, Audit for a lead
    2. Go to Leads tab
    3. Select the lead
    4. Click "Create Export Pack"
    5. Share ZIP with client

    ---

    ### 🔍 Search Scraper Tab
    **AI-Powered Web Research**
    - Search and synthesize information from multiple sources
    - Two modes: AI Extraction (uses LLM) or Markdown (raw content)
    - Custom JSON schemas for structured extraction
    - Source attribution

    ### 🌍 Enrich with Places Tab
    - Google Places API integration
    - Search businesses by text query
    - Get structured data: name, address, website, phone

    ### ✏️ Review & Edit Tab
    - Edit leads in spreadsheet interface
    - Update status, tags, and notes
    - Summarize leads with LLM

    ### 🛠️ SEO Tools Tab
    - **Content Audit:** Meta tags, headings, images, links
    - **SERP Tracker:** Track keyword positions
    - **Site Extractor:** Convert sites to markdown

    ---

    ### ⚙️ Settings

    **LLM Integration (Required for Consulting Features):**
    - Works with LM Studio: `https://lm.leophir.com/`
    - Works with Ollama: `http://localhost:11434`
    - Works with any OpenAI-compatible endpoint
    - API key optional for local models
    - Automatic `/v1` path handling

    **Configuration:**
    - Project name for organized exports
    - Language, country, city for localization
    - Concurrency (6-8 recommended)
    - Fetch timeout and crawl settings

    **Presets:**
    - Save/load configurations per niche or location
    - Vertical presets available in `presets/verticals/`

    ---

    ### 💡 Best Practices

    **For Consultants:**
    1. Use presets for each vertical (restaurant, retail, services)
    2. Always classify leads before outreach
    3. Build dossier before first contact
    4. Include dossier summary in outreach
    5. Run audit during discovery call
    6. Use export pack for client delivery

    **Performance:**
    - Keep concurrency low (6-8) to respect target sites
    - Use local LLM for privacy and cost savings
    - LM Studio recommended for best quality

    **Multilingual:**
    - Set language in settings (EN, FR, DE)
    - Outreach will use language-specific tone presets
    - Dossier and audit work in any language
    """)
