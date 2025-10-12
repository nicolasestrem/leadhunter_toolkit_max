def classify_lead(text: str, keywords: dict[str, list[str]]) -> list[str]:
    if not text:
        return []
    tags = []
    low = text.lower()
    for tag, words in (keywords or {}).items():
        if any(w.lower() in low for w in words):
            tags.append(tag)
    return sorted(set(tags))
