"""
Places Tab - Google Places API text search and enrichment
"""

import streamlit as st
import pandas as pd
from places import text_search as places_text_search, get_details as places_details
from utils_html import domain_of
from ui.components.progress_tracker import ProgressTracker
from ui.components.export_buttons import render_export_buttons
from constants import MIN_MAX_PLACES, MAX_MAX_PLACES, DEFAULT_MAX_PLACES


def render_places_tab(settings: dict):
    """
    Render the Google Places text search tab

    Args:
        settings: Application settings dict
    """
    st.subheader("Text search on Google Places")
    st.caption("Requires a valid API key. Uses /places:searchText and detail lookups.")

    # Input controls
    query_places = st.text_input("Places text query", placeholder="plombier à Toulouse")
    maxp = st.slider("Max places", MIN_MAX_PLACES, MAX_MAX_PLACES, DEFAULT_MAX_PLACES)
    go_places = st.button("Search Places")

    places_rows = []

    if go_places and query_places:
        key = settings.get("google_places_api_key", "")
        if not key:
            st.error("Please set your API key in Settings.")
        else:
            # Initialize progress tracker
            tracker = ProgressTracker()

            # Search places
            tracker.update(0.1, "🔍 Searching Google Places...")

            region = settings.get("google_places_region", "FR")
            lang = settings.get("google_places_language", "fr")
            plist = places_text_search(
                key, query_places, region=region, language=lang, max_results=maxp
            ) or []

            tracker.update(0.3, f"📍 Found {len(plist)} places, fetching details...")

            # Fetch details for each place
            for i, p in enumerate(plist):
                # Update progress periodically
                if i % 5 == 0 or i == len(plist) - 1:
                    tracker.update(
                        0.3 + (i / len(plist)) * 0.6,
                        f"📞 Fetching details {i+1}/{len(plist)}..."
                    )

                pid = p.get("id")
                det = places_details(key, pid, language=lang) if pid else {}

                row = {
                    "name": (p.get("displayName") or {}).get("text"),
                    "address": p.get("formattedAddress"),
                    "website": p.get("websiteUri") or det.get("websiteUri"),
                    "phone": det.get("internationalPhoneNumber"),
                    "place_id": pid
                }
                row["domain"] = domain_of(row["website"] or "") if row["website"] else None
                places_rows.append(row)

            tracker.complete(f"Found {len(places_rows)} places")
            st.success(f"✅ Retrieved {len(places_rows)} places with contact details")
            st.toast(f"Found {len(places_rows)} places", icon="📍")

    # Display results
    if places_rows:
        st.dataframe(pd.DataFrame(places_rows), width='stretch')

        # Export buttons
        render_export_buttons(
            places_rows,
            namespace="places",
            label_prefix="Export Places"
        )
