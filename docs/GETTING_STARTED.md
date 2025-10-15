# Getting Started with the Streamlit Toolkit

Lead Hunter Toolkit now ships with a Streamlit dashboard that brings all the
research, enrichment, and delivery workflows into one place. The quickest way
to explore the app is to launch it locally and walk through the Search Scraper
tab, which bundles the legacy scrapegraph.js features together with the new
contact discovery pipeline and site indexer.

## Prerequisites

- **Python 3.9 or newer.** Core dependencies such as Streamlit, pandas, and
  Playwright require modern Python versions.【F:requirements.txt†L1-L18】
- **macOS, Linux, or Windows.** The toolkit ships with activation commands for
  both POSIX shells and PowerShell, and Streamlit supports all three platforms
  out of the box.【F:README.md†L15-L33】
- **Baseline hardware.** Plan for concurrent HTTP requests and headless
  Chromium sessions spawned by Playwright, and close other heavy applications if
  you experience slowdowns.【F:fetch_dynamic.py†L10-L74】
- **Modern browser.** Streamlit serves the UI locally; Chrome, Edge, Firefox,
  or Safari all work well.

## Launch the application

1. Install the project dependencies (a virtual environment is recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   pip install -U pip
   pip install -r requirements.txt
   ```
2. Start the dashboard:
   ```bash
   streamlit run app.py
   ```
3. Streamlit will print a local URL (typically `http://localhost:8501`). Open
   it in your browser to access all tabs of the toolkit. The entry point wires
   the sidebar, settings persistence, and every tab from a single `main()`
   function so you do not need to write any glue code yourself.【F:app.py†L1-L88】

## Run web research with Search Scraper

Open the **Search Scraper** tab in the navigation bar once the app loads. The
panel exposes every control you need to go from a natural-language question to
structured answers or raw markdown copies of the pages that were fetched.

1. Provide your research question in the **Research Question or Query** text
   area and choose how many sources to fetch. The selector lets you switch
   between **AI Extraction** (LLM synthesis) and **Markdown** (concatenated page
   exports).【F:ui/tabs/search_scraper_tab.py†L34-L87】
2. (Optional) Tick **Use custom extraction schema (advanced)** to paste a JSON
   schema that guides the LLM output when you are in AI Extraction mode.【F:ui/tabs/search_scraper_tab.py†L89-L116】
3. Click **🔍 Search & Scrape**. Progress indicators will walk through search,
   fetching, conversion, and extraction steps while the underlying
   `SearchScraper` orchestrates the workflow.【F:ui/tabs/search_scraper_tab.py†L118-L195】【F:search_scraper.py†L15-L218】
4. Once the run finishes you can expand the **📚 Sources** section, review the
   synthesized insights or markdown payload, and export the results directly
   from the UI.【F:ui/tabs/search_scraper_tab.py†L150-L189】

## Use the contact discovery pipeline

Beneath the research results you will find the **Contact Discovery Pipeline**.
It can crawl a single website or execute a search query, consolidate all emails,
phone numbers, social profiles, and—new in this release—structured contact data
parsed from schema.org markup.

1. Pick **Website Crawl** or **Search Query** as the source mode.
2. Select which signals to capture by toggling **Extract Emails**, **Extract
   Phones**, **Extract Social**, and **Parse Structured Data**. The structured
   toggle enables schema.org JSON-LD and microdata parsing so contacts exposed
   in structured data snippets are merged alongside the traditional scraping
   output.【F:ui/tabs/search_scraper_tab.py†L203-L222】
3. Provide either the website URL or the search string, adjust crawl limits,
   and launch the pipeline. The Streamlit tab calls into the synchronous
   pipeline helpers so everything runs in one click.【F:ui/tabs/search_scraper_tab.py†L224-L305】【F:scraping/pipeline.py†L120-L218】
4. Review metrics, expand the contact lists, preview the processed markdown,
   and download the aggregated JSON payload once the run completes.【F:ui/tabs/search_scraper_tab.py†L307-L382】

## Enable and query the site indexer

Each Search Scraper run automatically syncs processed markdown into a lightweight
local vector index so you can revisit prior crawls without fetching the web
again. The index lives under `out/site_index` and is cached between sessions.

* The tab initialises a shared `SiteIndexer` instance backed by
  `embeddings.npy` and `metadata.json` files in that directory. The caption at
  the top of the Search Scraper panel shows how many chunks are currently
  available.【F:ui/tabs/search_scraper_tab.py†L39-L63】【F:indexing/site_indexer.py†L58-L116】
* During a scrape each page that successfully converts to markdown is chunked
  and added to the index together with metadata describing the prompt, mode,
  and source URL.【F:search_scraper.py†L128-L180】
* You can query the index from a notebook or script by instantiating
  `SiteIndexer("out/site_index")` and calling `.query("your question", top_k=5)`.
  The query method filters by domain or date when those parameters are supplied
  and returns rich metadata for each chunk so you can surface prior insights in
  custom workflows.【F:indexing/site_indexer.py†L24-L116】【F:indexing/site_indexer.py†L220-L283】

## Structured-data extraction controls

Structured-data parsing is enabled by default across the toolkit and can be
managed from two places:

* The global setting is stored in `config/defaults.yml` under
  `extraction.structured`, ensuring schema.org data is parsed even when you do
  not toggle the UI manually.【F:config/defaults.yml†L25-L34】
* The Search Scraper pipeline exposes a dedicated **Parse Structured Data**
  checkbox so you can turn structured extraction on or off for each run without
  touching configuration files.【F:ui/tabs/search_scraper_tab.py†L203-L215】

## Initial configuration and API security

Before running AI features, open the **Settings** sidebar and review three
areas that persist to `settings.json` for future sessions.【F:app.py†L1-L60】

1. **Search & Crawl.** Tune the search engine, timeouts, concurrency, and
   extraction toggles so your machine does not overload remote servers. Higher
   concurrency means more CPU usage locally and more simultaneous requests to
   target domains—start with the defaults and scale slowly.【F:sidebar_enhanced.py†L24-L112】【F:config/defaults.yml†L15-L36】
2. **Integrations.** Enter Google Places and Google Custom Search API keys only
   if you plan to enrich results with Google's data. The sidebar stores keys in
   password inputs and writes them to your local `settings.json`; keep that file
   private and prefer environment-specific copies on shared machines.【F:sidebar_enhanced.py†L114-L165】【F:app.py†L8-L44】
3. **LLM.** Choose between a local endpoint (LM Studio/Ollama) or a hosted
   provider. Local LLMs keep data on your machine, whereas cloud APIs send
   prompts to external services—decide based on compliance requirements before
   entering an API key.【F:sidebar_enhanced.py†L167-L230】【F:README.md†L35-L68】

## Dynamic rendering with Playwright

Some modern websites require JavaScript execution before their content is
available. Lead Hunter Toolkit supports Playwright-backed fetching for those
cases.

1. Install the browser runtime once on your machine:
   ```bash
   pip install playwright
   playwright install chromium
   ```
2. Open the **Settings → Search & Crawl** section to align timeout and
   concurrency limits with your hardware. Dynamic rendering launches headless
   Chromium instances, so start with modest concurrency (≤6) and raise it only
   if pages render reliably.【F:sidebar_enhanced.py†L60-L112】【F:fetch.py†L32-L108】
3. When authoring custom scripts or advanced automations, pass
   `dynamic_rendering=True` (and an allowlist if needed) into `fetch_many` or
   the crawling helpers. Rendered responses are cached with a `dynamic::`
   prefix so static and dynamic HTML never collide.【F:fetch.py†L32-L110】【F:crawl.py†L260-L314】【F:tests/test_dynamic_fetching.py†L12-L90】

If you only need dynamic rendering for specific domains, add them to the
allowlist arguments provided by the lower-level helpers before running your
custom scripts. The caching layer will ensure that subsequent runs reuse the
rendered HTML when possible.【F:fetch.py†L32-L108】

## Troubleshooting

- **Streamlit fails to start.** Confirm the virtual environment is active and
  reinstall dependencies with `pip install -r requirements.txt`. The root
  `README` includes the canonical sequence if you need to start over.【F:README.md†L15-L33】
- **`ModuleNotFoundError: playwright`.** Install the optional browser runtime
  and run `playwright install chromium`; the dynamic fetcher raises a clear
  error if the package is missing.【F:fetch_dynamic.py†L10-L74】
- **Chromium cannot launch or pages stay blank.** Lower the concurrency slider
  and increase timeouts in the sidebar so each headless browser has resources to
  render pages before the watchdog aborts the request.【F:sidebar_enhanced.py†L60-L112】【F:fetch.py†L32-L108】
- **Slow or blocked crawls.** Respect target sites by keeping concurrency
  modest and by using the built-in cache, which stores rendered pages for reuse
  without additional load.【F:crawl.py†L246-L314】【F:fetch.py†L32-L108】

With these steps you can run the Streamlit app end to end, perform AI-assisted
research, build contact lists, and revisit indexed findings without re-running
expensive crawls.
