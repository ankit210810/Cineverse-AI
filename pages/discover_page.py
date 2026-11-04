"""Discover and Search Page for Cineverse AI."""

import streamlit as st
from ui.components import render_hero, render_section_header, render_movie_card, render_html
from services.movie_service import (
    search_movies,
    get_all_genres,
    get_mood_movies,
    MOOD_GENRE_MAP
)


def render_discover_page(user: dict):
    user_id = user["user_id"]

    render_hero(
        title="Discover Cinema",
        subtitle="Explore over 1,600 curated films with multi-genre filters, era selectors, and emotional mood discovery."
    )

    # Tabs: General Search & Filter vs. Mood-Based Exploration
    tab1, tab2 = st.tabs(["🔍 Search & Filter", "🎭 Mood-Based Curation"])

    with tab1:
        # Check if user navigated here from top glass search bar
        global_term = st.session_state.pop("global_search_term", None)
        if global_term:
            st.session_state["search_title"] = global_term

        # Search & Filter Controls
        c_search, c_sort = st.columns([3, 1])
        with c_search:
            search_query = st.text_input("Search by Movie Title", placeholder="e.g. Star Wars, Toy Story, Pulp Fiction...", key="search_title")
        with c_sort:
            sort_by = st.selectbox(
                "Sort Results",
                options=["popularity", "rating", "year_desc", "year_asc", "title"],
                format_func=lambda x: {
                    "popularity": "Most Popular",
                    "rating": "Highest Rated",
                    "year_desc": "Newest Release",
                    "year_asc": "Classic / Oldest",
                    "title": "Title (A-Z)"
                }[x],
                key="sort_order"
            )

        with st.expander("Advanced Filters (Genres, Release Era, Rating Threshold)", expanded=False):
            f_col1, f_col2, f_col3 = st.columns([2, 2, 1.5])
            all_genres = get_all_genres()
            with f_col1:
                selected_genres = st.multiselect("Filter by Genres", options=all_genres, default=[], key="filter_genres")
            with f_col2:
                year_range = st.slider("Release Year Range", min_value=1920, max_value=2026, value=(1950, 2026), key="filter_years")
            with f_col3:
                min_rating = st.slider("Min Average Rating", min_value=0.0, max_value=5.0, value=0.0, step=0.5, key="filter_rating")

        # Query Database
        results, total_count = search_movies(
            query=search_query,
            genres=selected_genres,
            year_min=year_range[0],
            year_max=year_range[1],
            rating_min=min_rating if min_rating > 0 else None,
            sort_by=sort_by,
            limit=24,
            offset=0
        )

        st.caption(f"Found **{total_count}** matching films in Cineverse archive")

        if not results:
            st.info("No movies matched your current search parameters. Try expanding your filters.")
        else:
            # 4-column responsive grid
            grid_cols = st.columns(4)
            for idx, movie in enumerate(results):
                with grid_cols[idx % 4]:
                    render_movie_card(movie, user_id=user_id, show_explanation=False, key_prefix=f"disc_{idx}")

    with tab2:
        render_section_header("Mood Navigator", "Select your desired cinematic vibe", icon="✨")
        mood_keys = list(MOOD_GENRE_MAP.keys())
        active_mood = st.segmented_control("Emotional Tone", mood_keys, default="Mind-bending", key="active_mood_choice")

        if active_mood:
            info = MOOD_GENRE_MAP[active_mood]
            render_html(f"""
                <div style="background: rgba(64, 217, 232, 0.08); border-left: 3px solid #40D9E8; padding: 12px 16px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
                    <b style="color: #40D9E8; font-size: 1.05rem;">{info['badge']}</b><br/>
                    <span style="color: #D8C5FF; font-size: 0.9rem;">{info['tagline']}</span><br/>
                    <span style="color: #A0A5BA; font-size: 0.78rem;">Target Genres: {', '.join(info['genres'])}</span>
                </div>
            """)

            mood_results = get_mood_movies(active_mood, limit=12)
            m_cols = st.columns(4)
            for idx, movie in enumerate(mood_results):
                with m_cols[idx % 4]:
                    render_movie_card(movie, user_id=user_id, show_explanation=False, key_prefix=f"mood_p_{idx}")
