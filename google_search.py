import httpx
from typing import List

def google_sites(query: str, max_results: int, api_key: str, cx: str) -> List[str]:
    if not api_key or not cx:
        return []
    urls = []
    # Google returns 10 results per page
    remain = max_results
    start = 1
    while remain > 0 and start <= 91:  # API allows start 1..91
        num = min(10, remain)
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": num,
            "start": start,
        }
        r = httpx.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=20)
        if r.status_code != 200:
            break
        data = r.json()
        items = data.get("items") or []
        if not items:
            break
        for it in items:
            link = it.get("link")
            if link and link.startswith("http"):
                urls.append(link)
        start += num
        remain -= num
    # de-dup keeping order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out
