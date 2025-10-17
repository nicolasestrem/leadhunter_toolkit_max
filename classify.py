def classify_lead(text: str, keywords: dict[str, list[str]]) -> list[str]:
    """Classify a lead based on the presence of keywords in a given text.

    This function assigns tags to a lead by searching for predefined keywords.

    Args:
        text (str): The text to analyze.
        keywords (dict[str, list[str]]): A dictionary where keys are tags and
                                          values are lists of keywords.

    Returns:
        list[str]: A sorted list of unique tags that match the text.
    """
    if not text:
        return []
    tags = []
    low = text.lower()
    for tag, words in (keywords or {}).items():
        if any(w.lower() in low for w in words):
            tags.append(tag)
    return sorted(set(tags))
