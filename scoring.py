def score_lead(lead: dict, settings: dict) -> float:
    """Calculate a score for a lead based on a set of configurable weights.

    This function assigns a score to a lead by evaluating various attributes, such as
    the presence of contact information and a match with the target city.

    Args:
        lead (dict): The lead to score.
        settings (dict): The application settings, containing the scoring weights.

    Returns:
        float: The calculated score for the lead.
    """
    w = settings.get("scoring", {})
    score = 0.0
    score += w.get("email_weight", 2.0) * min(len(lead.get("emails", [])), 5)
    score += w.get("phone_weight", 1.0) * min(len(lead.get("phones", [])), 3)
    if lead.get("social"):
        score += w.get("social_weight", 0.5) * len([v for v in lead["social"].values() if v])
    title = (lead.get("name") or "").lower()
    if any(k in title for k in ["contact", "à propos", "about", "impressum"]):
        score += w.get("about_or_contact_weight", 1.0)
    if settings.get("city") and (lead.get("city") or "").lower() == settings["city"].lower():
        score += w.get("city_match_weight", 1.5)
    # bonus for .fr when country is FR etc.
    dom = (lead.get("domain") or "").lower()
    country = (settings.get("country") or "").lower()
    if country == "fr" and dom.endswith(".fr"):
        score += 0.5
    if country == "de" and dom.endswith(".de"):
        score += 0.5
    return round(score, 2)
