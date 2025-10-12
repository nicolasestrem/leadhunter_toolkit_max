# Lead hunting workflow • Max

1. Choose a project name in the sidebar. This namespaces your exports.
2. Save a preset for each niche or city so you can switch in one click.
3. In Hunt, either type a search query or paste a list of URLs.
4. The crawler fetches the home page plus up to N internal pages and prioritizes contact/about/legal pages.
5. The extractor gathers emails phones socials and tries to clean a company name from <title> or H1.
6. The classifier adds tags based on your keyword lists, which you can tune in `app.py` or extend later.
7. Review & Edit to update status, tags, notes. Export CSV, JSON or XLSX.
8. Enrich with Google Places (optional API key) to grab phones and websites quickly. Merge in your CRM.

## Robots and rate limits
The crawler checks robots.txt with a standard parser and avoids disallowed paths. Keep concurrency low and timeouts reasonable.
