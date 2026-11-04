"""Home Dashboard Page for Cineverse AI.

Features:
- Netflix-Style Cinematic Hero Slider / Featured Movie Carousel (auto-rotating, pause on hover, interactive arrows & indicators).
- Top Picks for You (Personalized & curated blockbuster row).
- Trending Now (Active real-time popularity ranking).
- Popular & Top Rated (Bayesian-smoothed high rating cinema).
- Because You Watched Interstellar (Sequential similarity cluster).
- Continue Watching (Real playback progress from database).
- Bottom Tri-Panel Row (Recently Watched, Why This Movie?, and Your Watch Stats).
- Live Recommendation Engine Output (PyTorch / Matrix Factorization deep dive).
"""

import streamlit as st
from ui.components import (
    render_html,
    render_top_bar,
    render_pick_card,
    render_tri_panel,
    render_movie_card
)
from ui.hero_slider import render_netflix_hero_slider
from ui.movie_carousel import render_movie_carousel
from services.movie_service import (
    get_movie,
    get_trending_movies,
    get_top_rated_movies,
    get_similar_movies,
    get_movies_by_ids
)
from services.history_service import get_continue_watching
from services.recommendation_service import get_recommendation_service
from services.user_service import get_user_taste_profile


def render_home_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    # 1. Netflix-Style Rotating Cinematic Hero Slider (Auto 7s + Pause on Hover + Full Controls)
    render_netflix_hero_slider()

    # 2. Section: "MUST WATCH TOP PICKS NOW" (Curated & Personalized Horizontal Carousel)
    curated_pick_ids = [10001, 10003, 10002, 10004, 10006, 10005, 50, 318, 296, 313]
    top_picks = []
    for pid in curated_pick_ids:
        m = get_movie(pid)
        if m:
            top_picks.append(m)
    if top_picks:
        render_movie_carousel(
            title_prefix="MUST WATCH TOP PICKS",
            highlight_word="NOW",
            movies=top_picks,
            user_id=user_id,
            carousel_id="carousel_top_picks",
            view_all_link="?nav=movies"
        )

    # 3. Section: "TRENDING MOVIES NOW" (Real Database Trending Movies Carousel)
    trending_movies = get_trending_movies(limit=12)
    if trending_movies:
        render_movie_carousel(
            title_prefix="TRENDING MOVIES",
            highlight_word="NOW",
            movies=trending_movies,
            user_id=user_id,
            carousel_id="carousel_trending",
            view_all_link="?nav=movies"
        )

    # 4. Section: "POPULAR & TOP RATED NOW" (Bayesian-Ranked Classics Carousel)
    top_rated = get_top_rated_movies(limit=12)
    if top_rated:
        render_movie_carousel(
            title_prefix="POPULAR & TOP RATED",
            highlight_word="NOW",
            movies=top_rated,
            user_id=user_id,
            carousel_id="carousel_top_rated",
            view_all_link="?nav=movies"
        )

    # 5. Section: "BECAUSE YOU WATCHED INTERSTELLAR NOW" (Content Similarity Carousel)
    similar_movies = get_similar_movies(10003, limit=12)
    if similar_movies:
        render_movie_carousel(
            title_prefix="BECAUSE YOU WATCHED INTERSTELLAR",
            highlight_word="NOW",
            movies=similar_movies,
            user_id=user_id,
            carousel_id="carousel_similar",
            view_all_link="?nav=movies"
        )

    # 6. Bottom Tri-Panel Row (Watch History, Why This Movie?, Taste Profile)
    taste = get_user_taste_profile(user_id)
    render_tri_panel(user_id=user_id, user_taste=taste)

    render_html("<div style='height: 24px;'></div>")

    # 7. Continue Watching (Real Playback Progress from Database)
    continue_items = get_continue_watching(user_id, limit=4)
    if continue_items:
        render_html("""
            <div class="section-headline-bar" id="history">
                <div class="section-headline-title">
                    <span style="color: #40D9E8;">▶</span> Continue Watching
                </div>
                <div style="font-size: 0.8rem; color: #7B809A;">Pick up right where you left off</div>
            </div>
        """)
        c_cols = st.columns(min(len(continue_items), 4))
        for i, item in enumerate(continue_items[:4]):
            with c_cols[i]:
                render_movie_card(item, user_id=user_id, show_explanation=False, key_prefix=f"cw_{item['movie_id']}_{i}")
                render_html(f"""
                    <div style="margin-top: -10px; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #A0A5BA;">
                            <span>{item['progress_pct']}% watched</span>
                            <span>{item['remaining_mins']}m left</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-fill" style="width: {item['progress_pct']}%;"></div>
                        </div>
                    </div>
                """)

    render_html("<div style='height: 20px;'></div>")

    # 8. Real Live Algorithmic Recommendations (PyTorch / Matrix Factorization)
    with st.expander("🤖 Live Recommendation Engine Output (Deep Dive)", expanded=False):
        algo = st.session_state.get("selected_algorithm", "Automatic Best Model")
        st.caption(f"Active Algorithm: **{algo}**")
        rec_service = get_recommendation_service()
        recs_res = rec_service.get_recommendations(user_id=user_id, algorithm=algo, limit=4)

        if recs_res.get("fallback_used"):
            render_html(f"""
                <div class="fallback-alert">
                    <span style="font-size: 1.3rem;">⚠️</span>
                    <div>
                        <b>Reliability Fallback Active:</b> {recs_res['fallback_reason']}<br/>
                        <span style="font-size: 0.8rem; opacity: 0.9;">Recommending consensus classics via Bayesian Popularity engine.</span>
                    </div>
                </div>
            """)

        engine_movies = recs_res.get("recommendations", [])
        if engine_movies:
            e_cols = st.columns(len(engine_movies))
            for i, movie in enumerate(engine_movies):
                with e_cols[i]:
                    render_movie_card(movie, user_id=user_id, show_explanation=True, key_prefix=f"live_eng_{movie['movie_id']}_{i}")
