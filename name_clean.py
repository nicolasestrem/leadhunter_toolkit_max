import re

def company_name_from_title(title: str | None) -> str | None:
    """Clean up a page title to extract a company name.

    This function uses a series of regular expressions to remove common suffixes,
    parentheticals, and prefixes from a page title to isolate the company name.

    Args:
        title (str | None): The page title to clean.

    Returns:
        str | None: The cleaned company name, or None if the title is invalid.
    """
    if not title:
        return None
    t = title.strip()
    t = re.sub(r"\s*[|·•\-–—]+\s*.*$", "", t)  # remove suffix after separators
    t = re.sub(r"\s+\(.*?\)$", "", t)  # remove trailing parentheses
    t = re.sub(r"^(Accueil|Home)\s*[:|\-]\s*", "", t, flags=re.I)
    if 2 <= len(t) <= 120:
        return t
    return None
