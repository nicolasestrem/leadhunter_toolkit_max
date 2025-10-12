"""
Unified progress tracking component for Streamlit UI
Provides consistent progress bars with status text across all tabs
"""

import streamlit as st
from typing import Callable, Any, List, Tuple


class ProgressTracker:
    """
    Reusable progress bar with status text

    Usage:
        tracker = ProgressTracker()
        tracker.update(0.5, "Processing...")
        tracker.complete("Done!")
    """

    def __init__(self):
        """Initialize progress bar and status text placeholders"""
        self.progress_bar = st.progress(0.0)
        self.status_text = st.empty()
        self._current_progress = 0.0

    def update(self, progress: float, message: str):
        """
        Update progress and status message

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Status message to display
        """
        self._current_progress = max(0.0, min(1.0, progress))
        self.progress_bar.progress(self._current_progress)
        self.status_text.text(message)

    def complete(self, message: str = "Complete!"):
        """
        Mark progress as complete

        Args:
            message: Completion message to display
        """
        self.progress_bar.progress(1.0)
        self.status_text.text(f"✓ {message}")

    def error(self, message: str):
        """
        Show error message

        Args:
            message: Error message to display
        """
        self.status_text.text(f"❌ {message}")

    def clear(self):
        """Clear progress bar and status text"""
        self.progress_bar.empty()
        self.status_text.empty()

    @staticmethod
    def track_phases(phases: List[Tuple[float, str, Callable]]) -> List[Any]:
        """
        Track multi-phase workflow with progress updates

        Args:
            phases: List of (progress, message, function) tuples

        Returns:
            List of results from each phase function

        Example:
            results = ProgressTracker.track_phases([
                (0.33, "Phase 1: Searching...", lambda: search()),
                (0.66, "Phase 2: Fetching...", lambda: fetch()),
                (1.0, "Phase 3: Processing...", lambda: process())
            ])
        """
        tracker = ProgressTracker()
        results = []

        for progress, message, func in phases:
            tracker.update(progress, message)
            try:
                result = func()
                results.append(result)
            except Exception as e:
                tracker.error(f"Error in phase: {str(e)}")
                raise

        tracker.complete("All phases complete!")
        return results
