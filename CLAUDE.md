# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lead Hunter Toolkit is a local lead generation and web research tool with a Streamlit GUI. It combines:
1. **Lead Hunting**: Discover and enrich business leads through web crawling, search engines, and Google Places API
2. **Search Scraper**: AI-powered web research that aggregates information from multiple sources

Key features: contact extraction (emails, phones, social links), scoring system, LLM-powered insights, and multi-format exports (CSV/JSON/XLSX).

## Running the Application

```bash
# Setup and run
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate    # Linux/Mac
pip install -U pip
pip install -r requirements.txt
streamlit run app.py
```

The main application is `app.py` (Streamlit GUI). The `app_llm.py` is a legacy entry point and should not be used.

## Architecture

### Core Pipeline Flow

1. **Search** → DuckDuckGo or Google Custom Search for initial URLs
2. **Crawl** → BFS crawl within same host, prioritizing contact/about pages (robots.txt aware)
3. **Extract** → Parse HTML for contact info, company names, social links
4. **Classify** → Keyword-based tagging for lead categorization
5. **Score** → Weighted scoring based on extracted data quality
6. **Export** → CSV/JSON/XLSX output to `out/` directory

### Key Modules

- **app.py**: Main Streamlit GUI with 5 tabs (Hunt, Search Scraper, Enrich with Places, Review & Edit, Session)
- **search_scraper.py**: AI-powered web research tool. Two modes: AI Extraction (LLM-based insights) and Markdown (raw content). Searches web, fetches pages, converts to markdown, optionally extracts structured data via LLM.
- **crawl.py**: BFS crawler with contact/about page prioritization. Respects same-host boundaries.
- **extract.py**: HTML extraction using selectolax. Extracts emails (including mailto:), phones, social links, company names from title/H1.
- **scoring.py**: Configurable weighted scoring system (emails, phones, social, city match, country domain bonus)
- **classify.py**: Simple keyword-based tagging system using DEFAULT_KEYWORDS dict in app.py
- **fetch.py**: Async HTTP fetching with caching (cache/ dir), concurrency control via semaphore
- **robots_util.py**: Robots.txt checker with in-memory cache per base URL
- **llm_client.py**: OpenAI-compatible client for lead summarization and SearchScraper AI extraction (supports local models via base_url)
- **places.py**: Google Places API integration for text search and detail lookups
- **exporters.py / exporters_xlsx.py**: Multi-format export handlers

### Data Models

**Lead structure** (models.py, schemas/lead.schema.json):
- name, domain, website, source_url
- emails[], phones[], social{} (facebook, instagram, linkedin, twitter, youtube)
- address, city, country, tags[], score, notes, when (timestamp)

### Configuration

**settings.json** stores:
- Search engine selection (ddg/google)
- Google API keys (CSE for search, Places for enrichment)
- Crawl parameters (max_sites, max_pages, concurrency, fetch_timeout, deep_contact)
- Extraction toggles (extract_emails, extract_phones, extract_social)
- Scoring weights (email_weight, phone_weight, social_weight, etc.)
- LLM settings (llm_base, llm_key, llm_model) for OpenAI-compatible endpoints
- Project namespace for exports
- Location context (country, language, city, radius_km)

**Presets**: JSON files in `presets/` directory for saving/loading niche-specific configurations.

## Important Implementation Details

### Crawling Strategy
- `crawl_site()` uses BFS up to max_pages within same netloc
- Prioritizes links containing contact/about keywords (CONTACT_WORDS in crawl.py:7)
- Filters through robots.txt before fetching
- Uses async batching with configurable concurrency

### Name Extraction
- Primary: `company_name_from_title()` cleans up common patterns from <title>
- Fallback: First <h1> tag content
- See name_clean.py for heuristic cleanup logic

### Scoring System
Lead scores are calculated in scoring.py with these defaults:
- email_weight: 2.0 per email (max 5 counted)
- phone_weight: 1.0 per phone (max 3 counted)
- social_weight: 0.5 per social platform
- about_or_contact_weight: 1.0 bonus if page title contains contact/about keywords
- city_match_weight: 1.5 bonus if city detected in text
- Country domain bonus: +0.5 for matching TLD (e.g., .fr when country=fr)

### Session State Management
Streamlit session_state["results"] holds the lead list throughout the session. The Review tab uses st.data_editor for inline editing with "Apply changes" button to persist edits.

### Caching
- HTML responses cached in `cache/` directory with SHA256-based filenames (fetch.py)
- Robots.txt cached in-memory per base URL (robots_util.py:_cache)

### Google APIs
- **Custom Search**: Requires API key + cx (engine ID) from console.cloud.google.com
- **Places**: Uses /places:searchText and detail lookups with field masks for efficiency

### LLM Integration
LLMClient supports any OpenAI-compatible endpoint (e.g., LM Studio, Ollama). Set llm_base (e.g., "http://localhost:1234" for LM Studio or "http://localhost:11434" for Ollama), and llm_model in settings. The `/v1` path is automatically appended to the base URL if not present. The llm_key is optional and defaults to "not-needed" for local LLMs that don't require authentication. Used for lead summarization in Review tab and SearchScraper AI extraction. The client includes proper error handling and null-safety checks for response parsing.

### SearchScraper Feature
SearchScraper is an AI-powered web research tool that searches, fetches, and analyzes multiple web pages based on a user's query.

**Architecture** (search_scraper.py):
- SearchScraperResult: Data class for results with mode, prompt, sources, extracted_data, markdown_content, error
- SearchScraper: Main class with two operation modes

**Workflow**:
1. Search web using existing search.py (DDG) or google_search.py
2. Fetch pages using fetch.py (async, with caching)
3. Convert HTML to markdown using markdownify library
4. Process based on mode:
   - AI Extraction: Use LLM to synthesize insights from all sources with citations
   - Markdown: Return concatenated markdown content with source metadata

**AI Extraction Mode**:
- Combines markdown from all sources (max 15K chars for LLM context)
- Supports optional custom JSON schema for structured extraction
- Builds comprehensive prompt with user question + content
- Calls LLM via llm_client.summarize_leads() (async wrapper)
- Returns synthesized answer with source citations

**Markdown Mode**:
- Faster, no LLM required
- Returns clean markdown from all fetched pages
- Includes source URLs and content length
- Useful for manual review or content migration

**GUI Integration** (app.py tab2):
- Text area for research question
- Slider for number of sources (3-20)
- Mode selector (AI Extraction / Markdown)
- Optional custom schema JSON editor
- Progress indicator with status updates
- Results display with expandable sources
- Export options (text for AI mode, markdown for markdown mode)

**Use Cases**:
- Research questions: aggregating information from multiple sources
- Competitive analysis: comparing features/products
- Market research: identifying trends
- Content creation: gathering source material
- Data collection: structured extraction with custom schemas

## Common Development Tasks

### Adding a new extraction field
1. Update Lead model in models.py
2. Update schemas/lead.schema.json
3. Add extraction logic in extract.py:extract_basic()
4. Update scoring logic in scoring.py if needed
5. Ensure field appears in DataFrame display (app.py line 289)

### Adding a new scoring weight
1. Add weight to default settings in sidebar (app.py)
2. Update scoring logic in scoring.py:score_lead()
3. Add to settings.json structure

### Adding a new tag classifier
1. Add keywords to DEFAULT_KEYWORDS dict in app.py:22
2. classify.py automatically uses all keyword categories

### Modifying crawl behavior
- Edit CONTACT_WORDS list in crawl.py:7 for prioritization
- Adjust should_visit() in crawl.py:9 for link filtering logic

## Notes

- Keep concurrency respectful of target sites (default: 6-8)
- Exports namespace by project name in settings
- User-Agent is "LeadHunter/1.0" (fetch.py, robots_util.py)
- Uses selectolax (not BeautifulSoup) for fast HTML parsing
- Google CSE and Places APIs are paid services with free tiers
