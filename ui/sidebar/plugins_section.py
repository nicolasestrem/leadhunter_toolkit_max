"""
Plugins section for sidebar.
Handles plugin management and display.
"""
import streamlit as st
from plugins import load_plugins


def render_plugins_section() -> None:
    """Render the plugins management section in the sidebar.

    This function displays the list of loaded plugins, their details, and provides
    a button to reload all plugins.
    """
    st.divider()
    st.subheader("Plugins")
    st.caption("Extend functionality with custom plugins")

    # Get loaded plugins
    loaded_plugins = st.session_state.get('plugins', [])

    if loaded_plugins:
        st.info(f"✓ {len(loaded_plugins)} plugin(s) loaded")

        # Show plugin details in expander
        with st.expander("Plugin Details", expanded=False):
            for plugin in loaded_plugins:
                st.markdown(
                    f"**{plugin.get('name', 'Unknown')}** "
                    f"v{plugin.get('version', '0.0.0')}"
                )
                st.caption(plugin.get('description', 'No description'))

                # Show hooks
                hooks = plugin.get('hooks', {})
                if hooks:
                    st.caption(f"Hooks: {', '.join(hooks.keys())}")

                # Show author if available
                if 'author' in plugin:
                    st.caption(f"Author: {plugin['author']}")

                st.markdown("---")
    else:
        st.caption("No plugins loaded")

    # Reload plugins button
    if st.button("Reload Plugins", help="Reload all plugins from plugins/ directory"):
        try:
            st.session_state.plugins = load_plugins()
            st.session_state.plugins_loaded = True
            st.success(f"Reloaded {len(st.session_state.plugins)} plugins")
            st.rerun()
        except Exception as e:
            st.error(f"Error reloading plugins: {e}")
