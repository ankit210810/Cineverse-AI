"""Watch History Page for Cineverse AI."""

import streamlit as st
from ui.components import render_hero, render_section_header, render_movie_card
from services.history_service import get_watch_history, add_to_watch_history, remove_from_history
from services.movie_service import search_movies


def render_history_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    render_hero(
        title="Viewing History",
        subtitle="Your persistent cinematic journey recorded in SQLite. Rate past screenings and track your chronological timeline.",
        user_name=display_name
    )

    # Manual Add to History Popover / Expander
    with st.expander("➕ Log a Movie You Recently Watched", expanded=False):
        c_search, c_btn = st.columns([3, 1])
        with c_search:
            manual_search = st.text_input("Search movie to log", placeholder="e.g. Jurassic Park, Fargo...", key="hist_manual_search")
        if manual_search:
            matched, _ = search_movies(query=manual_search, limit=5)
            if matched:
                pick_title = st.selectbox("Select exact film", [f"{m['movie_id']}: {m['title']} ({m['release_year']})" for m in matched], key="hist_pick_movie")
                if st.button("Log to Watch History", key="hist_confirm_add"):
                    picked_id = int(pick_title.split(":")[0])
                    add_to_watch_history(user_id, picked_id)
                    st.success("Successfully added to watch history!")
                    st.rerun()

    # Fetch History
    history = get_watch_history(user_id=user_id, limit=40)

    if not history:
        st.info("No watch history recorded for this profile yet. Log movies above or explore recommendations to begin building your timeline.")
        return

    render_section_header(f"Recorded Screenings ({len(history)} titles)", "Ordered by viewing timestamp", icon="🕒")

    grid_cols = st.columns(4)
    for idx, item in enumerate(history):
        with grid_cols[idx % 4]:
            render_movie_card(item, user_id=user_id, show_explanation=False, key_prefix=f"hist_{idx}")
            st.caption(f"Watched: {item.get('watched_at', 'Recently')[:10]}")
            if st.button("🗑️ Remove", key=f"del_hist_{item['history_id']}", help="Delete from history"):
                remove_from_history(item["history_id"])
                st.rerun()
