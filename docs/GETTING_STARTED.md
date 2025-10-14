# It worked! What else can I do with this?

SearchScraper is an LLM powered search and aggregation service with two modes:
- AI Extraction Mode default 10 credits per page
- Markdown Mode 2 credits per page

## Quick Start

### JavaScript
```js
import { searchScraper } from 'scrapegraph-js';
const apiKey = 'your-api-key';
const prompt = 'What is the latest version of Python and what are its main features?';
const response = await searchScraper(apiKey, prompt, 5);
console.log(response);
```

### Markdown Mode
```js
const response = await searchScraper(apiKey, 'Latest developments in artificial intelligence', 3, false);
console.log(response.markdown_content);
```

## Parameters
apiKey, prompt, numResults 3 to 20, extraction_mode boolean, schema object, mock boolean.

## Use cases
Research and analysis, data aggregation, content creation, cost effective scraping for bulk content.

## Dynamic Rendering Requirements

Some sites require JavaScript execution to expose their content. Enable Playwright-based
rendering by passing `dynamic_rendering=True` to `CrawlConfig`, `fetch_many`, or
`SearchScraper.search_and_scrape`. When dynamic rendering is enabled the toolkit will:

- Use [Playwright](https://playwright.dev/python/) with the Chromium engine.
- Cache rendered HTML separately from standard HTTP fetches to avoid stale data.
- Respect the existing concurrency, caching, and rate limiting settings.

Before enabling dynamic rendering install the browser runtime:

```bash
pip install playwright
playwright install chromium
```

Chromium downloads require roughly 150–200 MB of disk space. Expect each dynamic render to
consume more CPU and memory than a regular HTTP request.

Tests that exercise the Playwright integration are skipped by default. Run them explicitly
with:

```bash
pytest --run-playwright -m playwright
```
