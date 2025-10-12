"""
Centralized session state management for Streamlit app
Provides type-safe access to session state with clear key definitions
"""

import streamlit as st
from typing import Optional, List, Dict, Any


# Session state key constants
RESULTS = "results"
SEARCH_SCRAPER_RESULT = "search_scraper_result"
CLASSIFIED_LEADS = "classified_leads"
SELECTED_LEAD = "selected_lead"
OUTREACH_RESULT = "outreach_result"
DOSSIER_RESULT = "dossier_result"
DOSSIER_PAGES = "dossier_pages"
AUDIT_RESULT = "audit_result"
SINGLE_AUDIT = "single_audit"
QUICK_WINS_TASKS = "quick_wins_tasks"


def init_session_state():
    """
    Initialize all session state keys with default values
    Should be called once at app startup
    """
    defaults = {
        RESULTS: [],
        SEARCH_SCRAPER_RESULT: None,
        CLASSIFIED_LEADS: [],
        SELECTED_LEAD: None,
        OUTREACH_RESULT: None,
        DOSSIER_RESULT: None,
        DOSSIER_PAGES: None,
        AUDIT_RESULT: None,
        SINGLE_AUDIT: None,
        QUICK_WINS_TASKS: None,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# Getters - provide type-safe access to session state
def get_results() -> List[Dict[str, Any]]:
    """Get hunt results (leads)"""
    return st.session_state.get(RESULTS, [])


def get_search_scraper_result() -> Optional[Dict[str, Any]]:
    """Get search scraper result"""
    return st.session_state.get(SEARCH_SCRAPER_RESULT)


def get_classified_leads() -> List[Dict[str, Any]]:
    """Get classified leads from leads tab"""
    return st.session_state.get(CLASSIFIED_LEADS, [])


def get_selected_lead() -> Optional[Dict[str, Any]]:
    """Get currently selected lead"""
    return st.session_state.get(SELECTED_LEAD)


def get_outreach_result() -> Optional[Dict[str, Any]]:
    """Get outreach generation result"""
    return st.session_state.get(OUTREACH_RESULT)


def get_dossier_result() -> Optional[Dict[str, Any]]:
    """Get dossier generation result"""
    return st.session_state.get(DOSSIER_RESULT)


def get_dossier_pages() -> Optional[List[Dict[str, Any]]]:
    """Get dossier crawled pages"""
    return st.session_state.get(DOSSIER_PAGES)


def get_audit_result() -> Optional[Dict[str, Any]]:
    """Get audit result"""
    return st.session_state.get(AUDIT_RESULT)


def get_single_audit() -> Optional[Dict[str, Any]]:
    """Get single page audit result"""
    return st.session_state.get(SINGLE_AUDIT)


def get_quick_wins_tasks() -> Optional[List[Dict[str, Any]]]:
    """Get quick wins tasks from audit"""
    return st.session_state.get(QUICK_WINS_TASKS)


# Setters - provide controlled mutation of session state
def set_results(results: List[Dict[str, Any]]):
    """Set hunt results"""
    st.session_state[RESULTS] = results


def set_search_scraper_result(result: Optional[Dict[str, Any]]):
    """Set search scraper result"""
    st.session_state[SEARCH_SCRAPER_RESULT] = result


def set_classified_leads(leads: List[Dict[str, Any]]):
    """Set classified leads"""
    st.session_state[CLASSIFIED_LEADS] = leads


def set_selected_lead(lead: Optional[Dict[str, Any]]):
    """Set currently selected lead"""
    st.session_state[SELECTED_LEAD] = lead


def set_outreach_result(result: Optional[Dict[str, Any]]):
    """Set outreach generation result"""
    st.session_state[OUTREACH_RESULT] = result


def set_dossier_result(result: Optional[Dict[str, Any]]):
    """Set dossier generation result"""
    st.session_state[DOSSIER_RESULT] = result


def set_dossier_pages(pages: Optional[List[Dict[str, Any]]]):
    """Set dossier crawled pages"""
    st.session_state[DOSSIER_PAGES] = pages


def set_audit_result(result: Optional[Dict[str, Any]]):
    """Set audit result"""
    st.session_state[AUDIT_RESULT] = result


def set_single_audit(audit: Optional[Dict[str, Any]]):
    """Set single page audit result"""
    st.session_state[SINGLE_AUDIT] = audit


def set_quick_wins_tasks(tasks: Optional[List[Dict[str, Any]]]):
    """Set quick wins tasks from audit"""
    st.session_state[QUICK_WINS_TASKS] = tasks


# Helper functions for common patterns
def clear_consulting_results():
    """Clear all consulting pack results (outreach, dossier, audit)"""
    set_outreach_result(None)
    set_dossier_result(None)
    set_dossier_pages(None)
    set_audit_result(None)
    set_single_audit(None)
    set_quick_wins_tasks(None)


def has_results() -> bool:
    """Check if any hunt results exist"""
    return len(get_results()) > 0


def has_classified_leads() -> bool:
    """Check if any classified leads exist"""
    return len(get_classified_leads()) > 0


def has_selected_lead() -> bool:
    """Check if a lead is currently selected"""
    return get_selected_lead() is not None
