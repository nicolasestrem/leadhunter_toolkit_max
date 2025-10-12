import urllib.robotparser as urp
import httpx
from urllib.parse import urlparse

USER_AGENT = "LeadHunter/1.0"

_cache = {}

def robots_allowed(url: str) -> bool:
    try:
        p = urlparse(url)
        base = f"{p.scheme}://{p.netloc}"
        robots_url = base + "/robots.txt"
        if base in _cache:
            rp = _cache[base]
        else:
            rp = urp.RobotFileParser()
            try:
                r = httpx.get(robots_url, timeout=10, headers={"User-Agent": USER_AGENT})
                if r.status_code >= 400:
                    rp.parse([])
                else:
                    rp.parse(r.text.splitlines())
            except Exception:
                rp.parse([])
            rp.set_url(robots_url)
            _cache[base] = rp
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True
