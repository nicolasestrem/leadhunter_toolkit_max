from duckduckgo_search import DDGS

def ddg_sites(query: str, max_results: int = 10) -> list[str]:
    urls = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results, safesearch="moderate"):
            u = r.get("href") or r.get("url")
            if u and u.startswith("http"):
                urls.append(u)
    # simple de-dup
    seen = set()
    uniq = []
    for u in urls:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq
