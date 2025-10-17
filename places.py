import httpx
from retry_utils import retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)

BASE = "https://places.googleapis.com/v1"


@retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
def text_search(api_key: str, query: str, region: str = "FR", language: str = "fr", max_results: int = 10):
    """Search for places using the Google Places API text search.

    Args:
        api_key (str): Your Google Places API key.
        query (str): The search query.
        region (str): The region code (e.g., "FR", "DE", "US").
        language (str): The language code (e.g., "fr", "de", "en").
        max_results (int): The maximum number of results to return.

    Returns:
        list: A list of place dictionaries.
    """
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.websiteUri"
    }
    body = {"textQuery": query, "languageCode": language, "regionCode": region, "maxResultCount": max_results}

    try:
        logger.info(f"Searching Places API for: '{query}' (region: {region}, max: {max_results})")
        r = httpx.post(f"{BASE}/places:searchText", headers=headers, json=body, timeout=20)
        r.raise_for_status()

        places = r.json().get("places", [])
        logger.info(f"Places API search complete: {len(places)} results")
        return places

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error from Places API: {e}")
        return []
    except httpx.TimeoutException as e:
        logger.error(f"Timeout calling Places API: {e}")
        return []
    except Exception as e:
        logger.error(f"Error calling Places API: {e}")
        return []


@retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(httpx.HTTPError, httpx.TimeoutException))
def get_details(api_key: str, place_id: str, language: str = "fr"):
    """Get detailed information for a specific place from the Google Places API.

    Args:
        api_key (str): Your Google Places API key.
        place_id (str): The ID of the place to get details for.
        language (str): The language code for the results.

    Returns:
        dict: A dictionary containing the place's details.
    """
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,websiteUri,formattedAddress,internationalPhoneNumber"
    }

    try:
        logger.debug(f"Fetching place details for: {place_id}")
        r = httpx.get(f"{BASE}/{place_id}", headers=headers, params={"languageCode": language}, timeout=20)
        r.raise_for_status()

        details = r.json()
        logger.debug(f"Got details for: {details.get('displayName', {}).get('text', place_id)}")
        return details

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error fetching place details: {e}")
        return {}
    except httpx.TimeoutException as e:
        logger.error(f"Timeout fetching place details: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return {}
