# Getting Started with the Streamlit Toolkit

Lead Hunter Toolkit now ships with a Streamlit dashboard that brings all the
research, enrichment, and delivery workflows into one place. The quickest way
to explore the app is to launch it locally and walk through the Search Scraper
tab, which bundles the legacy scrapegraph.js features together with the new
contact discovery pipeline and site indexer.

## Launch the application

1. Install the project dependencies (a virtual environment is recommended):
   ```bash
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
   exports).【F:ui/tabs/search_scraper_tab.py†L33-L90】
2. (Optional) Tick **Use custom extraction schema (advanced)** to paste a JSON
   schema that guides the LLM output when you are in AI Extraction mode.【F:ui/tabs/search_scraper_tab.py†L92-L115】
3. Click **🔍 Search & Scrape**. Progress indicators will walk through search,
   fetching, conversion, and extraction steps while the underlying
   `SearchScraper` orchestrates the workflow.【F:ui/tabs/search_scraper_tab.py†L117-L156】【F:search_scraper.py†L15-L164】
4. Once the run finishes you can expand the **📚 Sources** section, review the
   synthesized insights or markdown payload, and export the results directly
   from the UI.【F:ui/tabs/search_scraper_tab.py†L158-L207】

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
   output.【F:ui/tabs/search_scraper_tab.py†L209-L243】
3. Provide either the website URL or the search string, adjust crawl limits,
   and launch the pipeline. The Streamlit tab calls into the synchronous
   pipeline helpers so everything runs in one click.【F:ui/tabs/search_scraper_tab.py†L245-L338】【F:scraping/pipeline.py†L122-L219】
4. Review metrics, expand the contact lists, preview the processed markdown,
   and download the aggregated JSON payload once the run completes.【F:ui/tabs/search_scraper_tab.py†L340-L402】

## Enable and query the site indexer

Each Search Scraper run automatically syncs processed markdown into a lightweight
local vector index so you can revisit prior crawls without fetching the web
again. The index lives under `out/site_index` and is cached between sessions.

* The tab initialises a shared `SiteIndexer` instance backed by
  `embeddings.npy` and `metadata.json` files in that directory. The caption at
  the top of the Search Scraper panel shows how many chunks are currently
  available.【F:ui/tabs/search_scraper_tab.py†L37-L50】【F:indexing/site_indexer.py†L58-L91】
* During a scrape each page that successfully converts to markdown is chunked
  and added to the index together with metadata describing the prompt, mode,
  and source URL.【F:search_scraper.py†L130-L156】
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
  not toggle the UI manually.【F:config/defaults.yml†L26-L34】
* The Search Scraper pipeline exposes a dedicated **Parse Structured Data**
  checkbox so you can turn structured extraction on or off for each run without
  touching configuration files.【F:ui/tabs/search_scraper_tab.py†L209-L243】

## Dynamic rendering with Playwright

Some modern websites require JavaScript execution before their content is
available. Lead Hunter Toolkit supports Playwright-backed fetching for those
cases.

1. Install the browser runtime once on your machine:
   ```bash
   pip install playwright
   playwright install chromium
   ```
2. Open the sidebar and switch to the **Search & Crawl** settings tab. This is
   the same panel that lets you fine-tune fetch timeouts, concurrency, and
   contact extraction defaults. In the enhanced sidebar build the
   **Dynamic rendering (Playwright)** toggle sits alongside these controls—flip
   it on to persist the preference to `settings.json`. If you are on an older
   layout, you can achieve the same effect by adding
   `"dynamic_rendering": true` to the saved settings file before launching the
   app.【F:sidebar_enhanced.py†L32-L116】【F:app.py†L8-L44】
3. With the toggle enabled, downstream helpers (such as `fetch_many` and
   `crawl_site`) receive `dynamic_rendering=True` and route eligible URLs
   through the Playwright workflow. Content is cached separately using a
   `dynamic::` cache key to avoid mixing rendered and static responses.【F:fetch.py†L50-L105】【F:crawl.py†L252-L303】

If you only need dynamic rendering for specific domains, add them to the
allowlist arguments provided by the lower-level helpers before running your
custom scripts. The caching layer will ensure that subsequent runs reuse the
rendered HTML when possible.【F:fetch.py†L56-L105】

With these steps you can run the Streamlit app end to end, perform AI-assisted
research, build contact lists, and revisit indexed findings without re-running
expensive crawls.
