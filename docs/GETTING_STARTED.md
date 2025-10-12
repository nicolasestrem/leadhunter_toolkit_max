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
