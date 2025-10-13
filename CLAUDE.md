# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lead Hunter Toolkit is a comprehensive local lead generation, web research, and SEO analysis tool with a Streamlit GUI. It combines:
1. **Lead Hunting**: Discover and enrich business leads through web crawling, search engines, and Google Places API
2. **Search Scraper**: AI-powered web research that aggregates information from multiple sources
3. **SEO Tools**: Content audit, SERP tracking, and site extraction capabilities

Key features: contact extraction (emails, phones, social links), scoring system, LLM-powered insights, SEO analysis, SERP position tracking, site-to-markdown extraction, and multi-format exports (CSV/JSON/XLSX).

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

The main application is `app.py` - a comprehensive Streamlit GUI with tabs for hunting, searching, SEO analysis, and lead management.

## Architecture

### Core Pipeline Flow

1. **Search** → DuckDuckGo or Google Custom Search for initial URLs
2. **Crawl** → BFS crawl within same host, prioritizing contact/about pages (robots.txt aware)
3. **Extract** → Parse HTML for contact info, company names, social links
4. **Classify** → Keyword-based tagging for lead categorization
5. **Score** → Weighted scoring based on extracted data quality
6. **Export** → CSV/JSON/XLSX output to `out/` directory

### Key Modules

- **app.py**: Main Streamlit GUI with 6 tabs (Hunt, Search Scraper, Enrich with Places, Review & Edit, SEO Tools, Session)
- **search_scraper.py**: AI-powered web research tool. Two modes: AI Extraction (LLM-based insights) and Markdown (raw content). Searches web, fetches pages, converts to markdown, optionally extracts structured data via LLM.
- **seo_audit.py**: Comprehensive SEO content auditor. Analyzes meta tags, headings, images, links, content quality. Optional LLM scoring for content quality assessment.
- **serp_tracker.py**: SERP position tracker for keywords. Tracks rankings over time, exports snapshots to CSV, supports DDG and Google CSE.
- **site_extractor.py**: Extract entire websites or sitemaps to markdown files. Supports sitemap.xml parsing and domain crawling.
- **crawl.py**: BFS crawler with contact/about page prioritization. Respects same-host boundaries.
- **extract.py**: HTML extraction using selectolax. Extracts emails (including mailto:), phones, social links, company names from title/H1.
- **scoring.py**: Configurable weighted scoring system (emails, phones, social, city match, country domain bonus)
- **classify.py**: Simple keyword-based tagging system using DEFAULT_KEYWORDS dict in app.py
- **fetch.py**: Async HTTP fetching with caching (cache/ dir), concurrency control via semaphore
- **cache_manager.py**: Cache management with expiration and size limits. Provides cleanup utilities and cache statistics.
- **robots_util.py**: Robots.txt checker with in-memory cache per base URL
- **llm_client.py**: OpenAI-compatible client with temperature and max_tokens control. Optimized for Qwen and local models.
- **places.py**: Google Places API integration for text search and detail lookups
- **logger.py**: Centralized logging module with file and console handlers
- **retry_utils.py**: Retry decorators with exponential backoff for sync/async functions
- **exporters.py / exporters_xlsx.py**: Multi-format export handlers

### Data Models

**Lead structure** (models.py, schemas/lead.schema.json):
- name, domain, website, source_url
- emails[], phones[], social{} (facebook, instagram, linkedin, twitter, youtube)
- address, city, country, tags[], status (new/contacted/qualified/rejected), score, notes, when (timestamp)

### Configuration

**settings.json** stores:
- Search engine selection (ddg/google)
- Google API keys (CSE for search, Places for enrichment)
- Crawl parameters (max_sites, max_pages, concurrency, fetch_timeout, deep_contact)
- Extraction toggles (extract_emails, extract_phones, extract_social)
- Scoring weights (email_weight, phone_weight, social_weight, etc.)
- LLM settings (llm_base, llm_key, llm_model, llm_temperature, llm_max_tokens) for OpenAI-compatible endpoints
- Project namespace for exports
- Location context (country, language, city, radius_km)

**Presets**: JSON files in `presets/` directory for saving/loading niche-specific configurations. UI controls in sidebar for easy load/save/delete.

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
- HTML responses cached in `cache/` directory with SHA256-based filenames
- Cache manager (cache_manager.py) provides expiration (30 days default) and size limits (500MB default)
- Cleanup utilities available: cleanup_expired(), cleanup_by_size(), cleanup_cache()
- Robots.txt cached in-memory per base URL (robots_util.py:_cache)
- All fetch operations use cache_manager for consistent expiration and size management

### Error Handling and Retry Logic
**All core modules now include comprehensive error handling:**
- **Retry Logic**: Exponential backoff retry for all API and HTTP requests (3 retries with 1s initial delay)
  - fetch.py: HTTP requests retry on timeout/connection errors
  - google_search.py: Google CSE API retries on HTTP errors
  - places.py: Google Places API retries with backoff
  - llm_client.py: LLM calls retry on failures (2 retries with 2s delay)
- **Logging**: All modules log to logs/leadhunter.log with console output
  - DEBUG: Detailed operation traces
  - INFO: Key operations and results
  - WARNING: Non-fatal issues
  - ERROR: Failures with stack traces
- **Error Recovery**: Graceful degradation on failures (empty results vs crashes)

### Google APIs
- **Custom Search**: Requires API key + cx (engine ID) from console.cloud.google.com
- **Places**: Uses /places:searchText and detail lookups with field masks for efficiency

### LLM Integration

**Dual-Model Architecture**: Lead Hunter Toolkit uses a two-model configuration for granular control of performance vs quality:

**Small Model (Mistral 7B)** - `mistralai/mistral-7b-instruct-v0.3`:
- **Purpose**: Fast extraction, SEO audit, categorization
- **Settings**: temp=0.4, top_k=30, top_p=0.9, max_tokens=4096
- **Use Cases**: AI-powered scraping, SEO audits, classification, structured JSON output

**Large Model (Llama 3 8B)** - `meta-llama-3-8b-instruct.gguf`:
- **Purpose**: French writing, outreach, advanced reasoning
- **Settings**: temp=0.6-0.7, top_k=40, top_p=0.9, max_tokens=8192
- **Use Cases**: Outreach generation, lead summarization, dossier building, complex synthesis

**Task-to-Model Mapping**:
| Feature | Model | Reason |
|---------|-------|--------|
| Search Scraper (AI) | Mistral 7B | Fast JSON extraction |
| SEO Content Audit | Mistral 7B | Structured analysis |
| Lead Classification | Mistral 7B | Deterministic tagging |
| Lead Summarization | Llama 3 8B | Advanced reasoning |
| French Outreach | Llama 3 8B | Creative writing |
| Dossier Building | Llama 3 8B | Complex synthesis |

**Configuration** (settings.json):
```json
{
  "llm_base": "https://lm.leophir.com/",
  "llm_model": "mistralai/mistral-7b-instruct-v0.3",
  "llm_temperature": 0.4,
  "llm_top_k": 40,
  "llm_top_p": 0.9,
  "llm_max_tokens": 2048
}
```

**Sampling Parameters**:
- **Temperature**: Controls randomness (0.0=deterministic, 2.0=creative) - Sent via API ✅
- **Top-K**: Limits vocabulary to top K tokens - ⚠️ Configure in LM Studio (not API parameter)
- **Top-P**: Nucleus sampling threshold (0.8-0.95 typical) - Sent via API ✅
- **Max Tokens**: Maximum response length - Sent via API ✅

**Important**: Top-K is NOT supported by OpenAI-compatible APIs. Configure it directly in LM Studio model settings (30 for Mistral 7B, 40 for Llama 3 8B).

**Unified Adapters**:
- **llm/adapter.py**: Modern adapter with full parameter support, async, and vision capabilities
- **llm_client.py**: Legacy client for backward compatibility

The `/v1` path is automatically appended to base URLs. The llm_key defaults to "not-needed" for local LLMs.

See [docs/DUAL_MODEL_CONFIGURATION.md](docs/DUAL_MODEL_CONFIGURATION.md) for comprehensive guide including:
- Detailed model specifications and benchmarks
- Parameter tuning guidelines
- Performance optimization tips
- Troubleshooting and migration guide

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

### SEO Tools Feature
Three integrated SEO analysis tools accessible from the SEO Tools tab:

**1. Content Audit** (seo_audit.py):
- Analyzes meta tags (title, description, OG tags, Twitter cards)
- Heading structure analysis (H1-H6)
- Image alt text coverage
- Internal vs external link analysis
- Word count and content quality metrics
- Schema.org structured data detection
- Technical SEO score (0-100)
- Optional LLM content quality scoring

**2. SERP Tracker** (serp_tracker.py):
- Track keyword positions in search results
- Support for DuckDuckGo and Google Custom Search
- Historical snapshot storage in serp_data/ directory
- Domain-specific position tracking
- CSV export for SERP data
- Comparison between snapshots to detect ranking changes

**3. Site Extractor** (site_extractor.py):
- Extract entire websites to markdown files
- Two modes: Sitemap URL or Domain Crawl
- Respects robots.txt
- Individual markdown file per page
- Combined markdown file for entire site
- Clean markdown conversion with markdownify
- Saved to out/site_{domain}/ directory

**GUI Integration** (app.py tab5):
- Three sub-tabs for each SEO tool
- Progress indicators and status updates
- Export options for all data
- Integration with LLM settings for content scoring

**Use Cases**:
- SEO audits for client sites
- Competitor content analysis
- Keyword rank tracking campaigns
- Site migration to markdown (e.g., for documentation)
- Content quality assessment

### Error Handling and Logging
- **logger.py**: Centralized logging with console and file handlers
- **retry_utils.py**: Decorators for automatic retry with exponential backoff
- Comprehensive error handling throughout all new modules
- Logs stored in logs/ directory

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
