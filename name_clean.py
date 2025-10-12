import re

def company_name_from_title(title: str | None) -> str | None:
    if not title:
        return None
    t = title.strip()
    t = re.sub(r"\s*[|·•\-–—]+\s*.*$", "", t)  # remove suffix after separators
    t = re.sub(r"\s+\(.*?\)$", "", t)  # remove trailing parentheses
    t = re.sub(r"^(Accueil|Home)\s*[:|\-]\s*", "", t, flags=re.I)
    if 2 <= len(t) <= 120:
        return t
    return None
