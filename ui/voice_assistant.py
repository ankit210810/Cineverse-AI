"""Voice AI Assistant Floating Component for Cineverse AI.

Renders a persistent floating pill button in the bottom-right corner of every page
matching the user reference design, with animated sparkle logo and direct navigation
to the Voice AI Assistant.
"""

import streamlit as st
from ui.components import render_html


def render_floating_ai_widget(user: dict):
    """Renders the persistent floating AI pill docked on the side of every page."""
    # Don't show floating pill if user is already on the AI Assistant page
    if "AI Assistant" in str(st.session_state.get("nav_selection", "")):
        return

    # Render floating pill as a native Streamlit button with fixed bottom-right dock styling
    with st.container():
        if st.button("✨  Cineverse AI", key="cineverse_floating_ai_btn", help="Open Cineverse AI Companion"):
            st.session_state["nav_selection"] = "✨ AI Assistant"
            if "cineverse_top_nav" in st.session_state:
                st.session_state["cineverse_top_nav"] = "✨ AI Assistant"
            st.rerun()
