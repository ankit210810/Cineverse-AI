"""Watchlist Page for Cineverse AI."""

import streamlit as st
from ui.components import render_hero, render_section_header, render_movie_card, render_html
from services.feedback_service import get_watchlist, remove_from_watchlist


def render_watchlist_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    render_hero(
        title="My Watchlist",
        subtitle="Your curated queue of upcoming films to enjoy. Easily add from recommendations or search.",
        user_name=display_name
    )

    items = get_watchlist(user_id=user_id, limit=50)

    if not items:
        render_html("""
            <div style="background: rgba(23, 22, 37, 0.6); border: 1px dashed rgba(140, 92, 255, 0.3); border-radius: 14px; padding: 40px; text-align: center; margin: 20px 0;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">🔖</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;">Your Watchlist is Empty</div>
                <div style="font-size: 0.9rem; color: #A0A5BA; max-width: 450px; margin: 0 auto 16px auto;">
                    Browse our Home dashboard or Discover catalog and click <b>+ List</b> to save films for later.
                </div>
            </div>
        """)
        return

    render_section_header(f"Saved Queue ({len(items)} movies)", "Ready for your next viewing session", icon="🔖")

    grid_cols = st.columns(4)
    for idx, movie in enumerate(items):
        with grid_cols[idx % 4]:
            render_movie_card(movie, user_id=user_id, show_explanation=False, key_prefix=f"wl_pg_{idx}")
