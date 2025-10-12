# Lead Hunter Toolkit • Max

A local lead hunting workflow with a polished Streamlit GUI, now extended for deeper crawl, presets, classifiers, XLSX export, and an editable review grid.

## Highlights
- BFS crawl within same host with contact/about prioritization
- Robots.txt aware by default
- Heuristic company name cleanup from <title> and H1
- Email + phone extraction including mailto: links
- Social discovery
- Keyword-based tagging
- Scoring with country-domain bonus
- Presets you can save and load per niche or city
- Project name to namespace exports
- Export to CSV, JSON and XLSX
- Optional Google Places enrichment

## Install and run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Keep concurrency respectful. Public sites have rate limits and policies.
- Exports land in the `out/` folder.
- Presets are saved under `presets/` as JSON files.


## Use Google instead of DuckDuckGo
The app defaults to DuckDuckGo text search. To use Google results, switch the **Search engine** in the sidebar to **google** and fill:
- **Google CSE API key**: from https://console.cloud.google.com/apis/credentials after enabling **Custom Search API**.
- **Google CSE cx**: create a **Programmable Search Engine** at https://programmablesearchengine.google.com/ and copy the `cx` id.

Notes:
- The Google Custom Search JSON API is a paid Google Cloud API with a free tier. Check quotas and pricing.
- Do not scrape Google HTML directly. Use the API to respect Google’s terms.
