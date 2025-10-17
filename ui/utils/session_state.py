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
    """Initialize all session state keys with their default values.

    This function should be called once at the beginning of the application's
    startup to ensure that all session state variables are properly initialized.
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
    """Get the hunt results (leads) from the session state.

    Returns:
        List[Dict[str, Any]]: A list of hunt results.
    """
    return st.session_state.get(RESULTS, [])


def get_search_scraper_result() -> Optional[Dict[str, Any]]:
    """Get the search scraper result from the session state.

    Returns:
        Optional[Dict[str, Any]]: The search scraper result.
    """
    return st.session_state.get(SEARCH_SCRAPER_RESULT)


def get_classified_leads() -> List[Dict[str, Any]]:
    """Get the classified leads from the session state.

    Returns:
        List[Dict[str, Any]]: A list of classified leads.
    """
    return st.session_state.get(CLASSIFIED_LEADS, [])


def get_selected_lead() -> Optional[Dict[str, Any]]:
    """Get the currently selected lead from the session state.

    Returns:
        Optional[Dict[str, Any]]: The currently selected lead.
    """
    return st.session_state.get(SELECTED_LEAD)


def get_outreach_result() -> Optional[Dict[str, Any]]:
    """Get the outreach generation result from the session state.

    Returns:
        Optional[Dict[str, Any]]: The outreach generation result.
    """
    return st.session_state.get(OUTREACH_RESULT)


def get_dossier_result() -> Optional[Dict[str, Any]]:
    """Get the dossier generation result from the session state.

    Returns:
        Optional[Dict[str, Any]]: The dossier generation result.
    """
    return st.session_state.get(DOSSIER_RESULT)


def get_dossier_pages() -> Optional[List[Dict[str, Any]]]:
    """Get the dossier's crawled pages from the session state.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of the dossier's crawled pages.
    """
    return st.session_state.get(DOSSIER_PAGES)


def get_audit_result() -> Optional[Dict[str, Any]]:
    """Get the audit result from the session state.

    Returns:
        Optional[Dict[str, Any]]: The audit result.
    """
    return st.session_state.get(AUDIT_RESULT)


def get_single_audit() -> Optional[Dict[str, Any]]:
    """Get the single page audit result from the session state.

    Returns:
        Optional[Dict[str, Any]]: The single page audit result.
    """
    return st.session_state.get(SINGLE_AUDIT)


def get_quick_wins_tasks() -> Optional[List[Dict[str, Any]]]:
    """Get the quick wins tasks from the session state.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of quick wins tasks.
    """
    return st.session_state.get(QUICK_WINS_TASKS)


# Setters - provide controlled mutation of session state
def set_results(results: List[Dict[str, Any]]):
    """Set the hunt results in the session state.

    Args:
        results (List[Dict[str, Any]]): The hunt results to set.
    """
    st.session_state[RESULTS] = results


def set_search_scraper_result(result: Optional[Dict[str, Any]]):
    """Set the search scraper result in the session state.

    Args:
        result (Optional[Dict[str, Any]]): The search scraper result to set.
    """
    st.session_state[SEARCH_SCRAPER_RESULT] = result


def set_classified_leads(leads: List[Dict[str, Any]]):
    """Set the classified leads in the session state.

    Args:
        leads (List[Dict[str, Any]]): The classified leads to set.
    """
    st.session_state[CLASSIFIED_LEADS] = leads


def set_selected_lead(lead: Optional[Dict[str, Any]]):
    """Set the currently selected lead in the session state.

    Args:
        lead (Optional[Dict[str, Any]]): The lead to set as selected.
    """
    st.session_state[SELECTED_LEAD] = lead


def set_outreach_result(result: Optional[Dict[str, Any]]):
    """Set the outreach generation result in the session state.

    Args:
        result (Optional[Dict[str, Any]]): The outreach result to set.
    """
    st.session_state[OUTREACH_RESULT] = result


def set_dossier_result(result: Optional[Dict[str, Any]]):
    """Set the dossier generation result in the session state.

    Args:
        result (Optional[Dict[str, Any]]): The dossier result to set.
    """
    st.session_state[DOSSIER_RESULT] = result


def set_dossier_pages(pages: Optional[List[Dict[str, Any]]]):
    """Set the dossier's crawled pages in the session state.

    Args:
        pages (Optional[List[Dict[str, Any]]]): The list of crawled pages to set.
    """
    st.session_state[DOSSIER_PAGES] = pages


def set_audit_result(result: Optional[Dict[str, Any]]):
    """Set the audit result in the session state.

    Args:
        result (Optional[Dict[str, Any]]): The audit result to set.
    """
    st.session_state[AUDIT_RESULT] = result


def set_single_audit(audit: Optional[Dict[str, Any]]):
    """Set the single page audit result in the session state.

    Args:
        audit (Optional[Dict[str, Any]]): The single page audit result to set.
    """
    st.session_state[SINGLE_AUDIT] = audit


def set_quick_wins_tasks(tasks: Optional[List[Dict[str, Any]]]):
    """Set the quick wins tasks in the session state.

    Args:
        tasks (Optional[List[Dict[str, Any]]]): The list of quick wins tasks to set.
    """
    st.session_state[QUICK_WINS_TASKS] = tasks


# Helper functions for common patterns
def clear_consulting_results():
    """Clear all consulting pack results from the session state.

    This function is a convenience helper to reset the state related to outreach,
    dossiers, and audits.
    """
    set_outreach_result(None)
    set_dossier_result(None)
    set_dossier_pages(None)
    set_audit_result(None)
    set_single_audit(None)
    set_quick_wins_tasks(None)


def has_results() -> bool:
    """Check if any hunt results exist in the session state.

    Returns:
        bool: True if there are hunt results, False otherwise.
    """
    return len(get_results()) > 0


def has_classified_leads() -> bool:
    """Check if any classified leads exist in the session state.

    Returns:
        bool: True if there are classified leads, False otherwise.
    """
    return len(get_classified_leads()) > 0


def has_selected_lead() -> bool:
    """Check if a lead is currently selected in the session state.

    Returns:
        bool: True if a lead is selected, False otherwise.
    """
    return get_selected_lead() is not None
