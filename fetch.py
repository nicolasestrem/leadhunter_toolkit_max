import httpx, asyncio, os, hashlib, time
from selectolax.parser import HTMLParser

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

def cache_path(url: str) -> str:
    return os.path.join(CACHE_DIR, _key(url) + ".html")

async def fetch_one(client: httpx.AsyncClient, url: str, timeout: int = 15) -> str:
    try:
        r = await client.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "LeadHunter/1.0"})
        r.raise_for_status()
        return r.text
    except Exception:
        return ""

async def fetch_many(urls: list[str], timeout: int = 15, concurrency: int = 6, use_cache: bool = True) -> dict[str, str]:
    out = {}
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        async def task(url):
            if use_cache:
                p = cache_path(url)
                if os.path.exists(p):
                    try:
                        out[url] = open(p, "r", encoding="utf-8", errors="ignore").read()
                        return
                    except Exception:
                        pass
            async with sem:
                html = await fetch_one(client, url, timeout)
                out[url] = html
                if html and use_cache:
                    try:
                        open(cache_path(url), "w", encoding="utf-8").write(html)
                    except Exception:
                        pass
        await asyncio.gather(*(task(u) for u in urls))
    return out

def extract_links(html: str, base_url: str) -> list[str]:
    try:
        tree = HTMLParser(html)
        hrefs = []
        for a in tree.css("a[href]"):
            hrefs.append(a.attributes.get("href"))
        # basic join left to caller
        return hrefs
    except Exception:
        return []

def text_content(html: str) -> str:
    try:
        tree = HTMLParser(html)
        return tree.text(separator=" ", strip=True)
    except Exception:
        return ""
