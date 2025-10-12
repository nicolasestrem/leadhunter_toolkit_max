"""
Cache section for sidebar.
Handles cache management and display.
"""
import streamlit as st
from cache_manager import get_cache_stats, cleanup_cache, clear_all_cache


def render_cache_section() -> None:
    """
    Render cache management section.

    Shows cache statistics and provides cleanup/clear functionality.
    """
    st.divider()
    st.subheader("Cache Management")
    st.caption("Manage HTTP response cache")

    try:
        cache_stats = get_cache_stats()
        st.metric("Cache Files", f"{cache_stats['file_count']} files")
        st.metric("Cache Size", f"{cache_stats['total_size_mb']:.1f} MB")
        st.caption(
            f"Max size: {cache_stats['max_size_mb']} MB • "
            f"Max age: {cache_stats['max_age_days']} days"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cleanup Expired", help="Remove expired cache files"):
                result = cleanup_cache()
                st.success(
                    f"Removed {result['expired_deleted']} expired files and "
                    f"{result['size_deleted']} oversized files"
                )
                st.rerun()
        with col2:
            if st.button(
                "Clear All Cache",
                type="secondary",
                help="Delete all cached files"
            ):
                deleted = clear_all_cache()
                st.success(f"Cleared cache: {deleted} files deleted")
                st.rerun()
    except Exception as e:
        st.error(f"Cache error: {e}")
