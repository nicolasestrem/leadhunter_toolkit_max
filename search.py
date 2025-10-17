from duckduckgo_search import DDGS

def ddg_sites(query: str, max_results: int = 10) -> list[str]:
    """Search DuckDuckGo for a given query and return a list of result URLs.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of results to return.

    Returns:
        list[str]: A list of unique result URLs.
    """
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
