import httpx, os, json

BASE = "https://places.googleapis.com/v1"

def text_search(api_key: str, query: str, region: str = "FR", language: str = "fr", max_results: int = 10):
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.websiteUri"
    }
    body = {"textQuery": query, "languageCode": language, "regionCode": region, "maxResultCount": max_results}
    try:
        r = httpx.post(f"{BASE}/places:searchText", headers=headers, json=body, timeout=20)
        r.raise_for_status()
        return r.json().get("places", [])
    except Exception:
        return []

def get_details(api_key: str, place_id: str, language: str = "fr"):
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,websiteUri,formattedAddress,internationalPhoneNumber"
    }
    try:
        r = httpx.get(f"{BASE}/{place_id}", headers=headers, params={"languageCode": language}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}
