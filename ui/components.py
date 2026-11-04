"""UI Components and Visual Blocks for Cineverse AI.

Features the celestial astronaut hero, personalized picks cards,
why-this-movie influence breakdowns, taste profile film reel motif,
and custom HTML renderers that prevent raw code block output.
"""

import streamlit as st
import plotly.graph_objects as go
import base64
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Any
from services.feedback_service import (
    is_in_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_feedback,
    set_feedback,
    remove_feedback,
    rate_movie
)
from services.poster_service import get_movie_poster_url
from services.video_service import get_movie_video_info

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NAV_LOGO_PATH = PROJECT_ROOT / "assets" / "cineverse_nav_logo.png"
PLAY_ICON_PATH = PROJECT_ROOT / "assets" / "cineverse_play_icon.png"
EMBLEM_PATH = PROJECT_ROOT / "assets" / "cineverse_emblem.png"
LOGO_PATH = PROJECT_ROOT / "assets" / "cineverse_logo.png"
_CACHED_LOGO_B64 = None


def get_logo_base64() -> str:
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64 is None:
        target = NAV_LOGO_PATH if NAV_LOGO_PATH.exists() else (EMBLEM_PATH if EMBLEM_PATH.exists() else (LOGO_PATH if LOGO_PATH.exists() else None))
        if target:
            _CACHED_LOGO_B64 = base64.b64encode(target.read_bytes()).decode("utf-8")
        else:
            _CACHED_LOGO_B64 = ""
    return _CACHED_LOGO_B64


def render_html(content: str):
    """Safely renders HTML without Markdown indentation treating lines as code blocks."""
    if hasattr(st, "html"):
        st.html(content)
    else:
        clean_lines = [line.strip() for line in content.splitlines()]
        st.markdown("\n".join(clean_lines), unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, user_name: Optional[str] = None):
    """Renders a cinematic hero banner."""
    greeting = f"Welcome back, <span style='color: #40D9E8;'>{user_name}</span>" if user_name else "Welcome to Cineverse AI"
    render_html(f"""
        <div class="cineverse-hero">
            <div style="font-size: 0.85rem; color: #B77BFF; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">
                {greeting}
            </div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
    """)


def render_section_header(title: str, subtitle: Optional[str] = None, icon: str = "🎬"):
    """Renders a section header divider."""
    sub_html = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ""
    render_html(f"""
        <div class="section-header">
            <div class="section-title"><span>{icon}</span> {title}</div>
            {sub_html}
        </div>
    """)


def render_logo():
    """Renders the custom cinematic play-button logo and wordmark."""
    render_html("""
        <div class="cineverse-logo-container">
            <div class="cineverse-logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
            </div>
            <div>
                <div class="cineverse-wordmark">Cineverse</div>
                <div class="cineverse-tagline">AI RECOMMENDATION PLATFORM</div>
            </div>
        </div>
    """)


def render_top_bar(current_user: Dict[str, Any]):
    """Renders the top application search and user avatar bar matching the second reference screenshot."""
    user_initial = "A"
    display_name = current_user.get("display_name") or current_user.get("username") or "User"
    if display_name:
        user_initial = display_name[0].upper()

    col_search, col_actions = st.columns([5.2, 0.8], gap="medium")
    with col_search:
        search_query = st.text_input(
            "Search",
            placeholder="🔍 Search for movies, genres, or moods...",
            label_visibility="collapsed",
            key="home_global_search"
        )
        if search_query:
            st.session_state["global_search_term"] = search_query
            st.session_state["nav_selection"] = "🧭 Mood Discovery"

    with col_actions:
        b_c1, b_c2 = st.columns([1, 1])
        with b_c1:
            render_html("""
                <div class="top-bell-btn" title="Notifications">
                    🔔
                </div>
            """)
        with b_c2:
            if st.button(user_initial, key="top_user_avatar_btn", help=f"Profile: {display_name} (Admin)"):
                st.session_state["nav_selection"] = "👤 Profile"
                st.rerun()


def render_duckshow_navbar(current_user: Dict[str, Any]):
    """Renders the transparent horizontal streaming navbar matching the user's reference."""
    current_sel = st.session_state.get("nav_selection", "🏠 Home")
    display_name = current_user.get("display_name") or current_user.get("username") or "Ankit Kumar"

    # Compute initials dynamically for any logged-in user (e.g. Sonu Kumar -> SK, Ankit Kumar -> AK)
    initials = "U"
    if display_name:
        parts = display_name.strip().split()
        if len(parts) >= 2:
            initials = f"{parts[0][0]}{parts[-1][0]}".upper()
        elif len(parts) == 1:
            initials = parts[0][:2].upper()

    # Dynamic vibrant gradient per user name
    gradient_presets = [
        "linear-gradient(135deg, #1C1535 0%, #2A1E50 50%, #3D2670 100%)",
        "linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #3B82F6 100%)",
        "linear-gradient(135deg, #1E1B4B 0%, #4338CA 50%, #6366F1 100%)",
        "linear-gradient(135deg, #2E1065 0%, #6B21A8 50%, #A855F7 100%)",
        "linear-gradient(135deg, #3B0764 0%, #701A75 50%, #C026D3 100%)",
        "linear-gradient(135deg, #142A27 0%, #0F766E 50%, #14B8A6 100%)",
    ]
    user_bg_gradient = gradient_presets[abs(hash(display_name)) % len(gradient_presets)]
    avatar_url = current_user.get("avatar_url") or current_user.get("picture")

    is_admin = current_user.get("user_type") == "admin" or current_user.get("is_admin", True) or st.session_state.get("is_admin", True)

    nav_items = [
        ("Home", "🏠 Home", "home"),
        ("Series", "🎬 Series", "series"),
        ("Movies", "📽️ Movies", "movies"),
        ("My List", "📺 My List", "my_list"),
        ("AI Assistant", "✨ AI Assistant", "assistant"),
    ]
    if is_admin:
        nav_items.append(("Admin", "🛡️ Admin Portal", "admin"))

    logo_b64 = get_logo_base64()

    with st.container(key="duckshow_navbar_container"):
        col_brand, col_menu, col_right = st.columns([1.5, 6.7, 1.8], vertical_alignment="center")

        with col_brand:
            logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="cineverse-nav-full-logo" alt="Cineverse" />' if logo_b64 else '<div class="cineverse-nav-wordmark"><span class="cineverse-word-cine">Cine</span><span class="cineverse-word-verse">verse</span></div>'
            render_html(f"""
                <a href="?nav=home" target="_self" class="cineverse-brand-lockup-link" title="Cineverse AI Home">
                    <div class="cineverse-brand-lockup">
                        {logo_img_tag}
                    </div>
                </a>
            """)

        with col_menu:
            col_weights = [1.0, 1.0, 1.0, 1.1, 1.3, 1.0] if is_admin else [1.0, 1.0, 1.0, 1.1, 1.3]
            menu_cols = st.columns(col_weights, vertical_alignment="center")
            for i, (label, target, slug) in enumerate(nav_items):
                with menu_cols[i]:
                    is_active = (current_sel == target or (target == "🏠 Home" and current_sel in ["🏠 Home", "Home"]))
                    btn_kind = "primary" if is_active else "secondary"
                    if st.button(label, key=f"dnav_item_{slug}", type=btn_kind, use_container_width=True):
                        st.session_state["nav_selection"] = target
                        st.rerun()

        with col_right:
            c_search, c_bell, c_avatar = st.columns([1, 1, 1], vertical_alignment="center")
            with c_search:
                with st.popover("🔍", help="Search movies, genres & moods", key="nav_search_popover"):
                    search_query = st.text_input(
                        "Search",
                        placeholder="Search movies, genres...",
                        label_visibility="collapsed",
                        key="popover_search_box"
                    )
                    if search_query:
                        st.session_state["global_search_term"] = search_query
                        st.session_state["catalog_search_query"] = search_query
                        st.session_state["nav_selection"] = "📽️ Movies"
                        st.rerun()

            with c_bell:
                render_html("""
                    <div class="duckshow-bell-icon" title="Notifications">
                        🔔
                        <span class="duckshow-bell-count">3</span>
                    </div>
                """)
            with c_avatar:
                role_label = "Administrator" if is_admin else "Member"
                if avatar_url:
                    avatar_content = f'<img src="{avatar_url}" alt="{display_name}" class="user-avatar-img" />'
                else:
                    avatar_content = f'<span class="user-avatar-text">{initials}</span>'

                render_html(f"""
                    <a href="?nav=profile" target="_self" class="duckshow-profile-lockup" title="Profile: {display_name} ({role_label})">
                        <div class="user-avatar-pfp" style="background: {user_bg_gradient};">
                            {avatar_content}
                        </div>
                    </a>
                """)


def render_celestial_hero(user_name: Optional[str] = None):
    """Renders the celestial astronaut hero banner matching the second reference screenshot."""
    render_html("""
        <div class="celestial-hero-wrapper">
            <div class="celestial-hero-overlay">
                <div class="hero-content-left">
                    <div class="hero-intelligent-badge">
                        <span>★</span> Intelligent Recommendations
                    </div>
                    <div class="hero-title-main">Your next story.</div>
                    <div class="hero-title-gradient">Already remembered.</div>
                    <div class="hero-desc">
                        Discover movies, get personalized recommendations, and let Cineverse AI understand your taste.
                    </div>
                    <div class="hero-actions-row">
                        <a href="?play=hero" target="_self" class="hero-btn-play">
                            <span>▶</span> Play Demo
                        </a>
                        <a href="#why-this-movie" class="hero-btn-more-info">
                            <span>ⓘ</span> More Info
                        </a>
                    </div>
                </div>
            </div>
        </div>
    """)


def render_pick_card(
    movie: Dict[str, Any],
    user_id: int,
    subtitle: str = "2010 • Sci-Fi",
    key_prefix: str = "pick"
):
    """Renders a movie card matching the second reference screenshot with Watch Demo and Add to List."""
    mid = movie["movie_id"]
    title = movie["title"].split("(")[0].strip()
    poster_url = get_movie_poster_url(mid, movie["title"])
    if not poster_url:
        poster_url = "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"

    in_wl = is_in_watchlist(user_id, mid)

    with st.container(key=f"pick_card_wrapper_{key_prefix}_{mid}"):
        render_html(f"""
            <div class="pick-poster-wrap">
                <img src="{poster_url}" alt="{title}" class="pick-poster-img" loading="lazy" />
            </div>
        """)

        c_meta, c_watch, c_btn = st.columns([0.48, 0.32, 0.20])
        with c_meta:
            render_html(f"""
                <div class="pick-meta-info" style="padding-top: 4px;">
                    <div class="pick-card-title" title="{title}">{title}</div>
                    <div class="pick-card-subtitle">{subtitle}</div>
                </div>
            """)
        with c_watch:
            with st.container(key=f"pick_watch_box_{key_prefix}_{mid}"):
                if st.button("▶ Watch", key=f"{key_prefix}_watch_{mid}", help=f"Watch 15s+ Demo of {title}"):
                    st.session_state["cinema_playing_movie"] = movie
                    st.rerun()
        with c_btn:
            wl_icon = "✓" if in_wl else "+"
            wl_help = "Remove from My List" if in_wl else "Add to My List"
            with st.container(key=f"pick_btn_box_{key_prefix}_{mid}"):
                if st.button(wl_icon, key=f"{key_prefix}_wl_{mid}", help=wl_help):
                    if in_wl:
                        remove_from_watchlist(user_id, mid)
                    else:
                        add_to_watchlist(user_id, mid)
                    st.rerun()


def render_tri_panel(user_id: int, user_taste: Dict[str, Any]):
    """Renders the 3-panel widgets row (Recently Watched, Why This Movie?, and Your Watch Stats) matching the screenshot."""
    c1, c2, c3 = st.columns([1.1, 1.25, 1.1])

    with c1:
        render_html("""
            <div class="tri-card">
                <div>
                    <div class="tri-card-header">
                        <div class="tri-card-title"><span style="color: #8B2CF5;">🕒</span> Recently Watched</div>
                        <a href="#history" class="section-headline-link">View all ➔</a>
                    </div>
                    <div class="history-mini-row">
                        <img src="https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg" class="history-mini-poster" title="Interstellar" />
                        <img src="https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg" class="history-mini-poster" title="The Matrix" />
                        <img src="https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg" class="history-mini-poster" title="Inception" />
                        <img src="https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg" class="history-mini-poster" title="Dune" />
                    </div>
                </div>
            </div>
        """)

    with c2:
        render_html("""
            <div class="tri-card" id="why-this-movie">
                <div>
                    <div class="tri-card-header">
                        <div class="tri-card-title"><span style="color: #C026FF;">✨</span> Why this movie?</div>
                    </div>
                    <div class="influence-content-wrap">
                        <img src="https://image.tmdb.org/t/p/w500/x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg" class="influence-thumb" alt="Arrival" />
                        <div class="influence-details">
                            <div class="influence-desc" style="font-size: 0.88rem; line-height: 1.5; color: #D8C5FF;">
                                Based on your love for <b>Interstellar</b>, we think you'll enjoy <b>Arrival</b>.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """)

    with c3:
        render_html("""
            <div class="tri-card">
                <div>
                    <div class="tri-card-header">
                        <div class="tri-card-title"><span style="color: #8B2CF5;">📊</span> Your Watch Stats</div>
                    </div>
                    <div class="watch-stats-wrap">
                        <div class="stat-box">
                            <div class="stat-val-row">
                                <span class="stat-icon-purple">▶</span>
                                <span>24</span>
                            </div>
                            <div class="stat-label">Movies</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-val-row">
                                <span class="stat-icon-violet">🕒</span>
                                <span>56h</span>
                            </div>
                            <div class="stat-label">Watched</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-val-row">
                                <span class="stat-icon-yellow">★</span>
                                <span>4.5</span>
                            </div>
                            <div class="stat-label">Rating</div>
                        </div>
                    </div>
                </div>
            </div>
        """)


def render_movie_card(
    movie: Dict[str, Any],
    user_id: int,
    show_explanation: bool = True,
    key_prefix: str = "card"
):
    """Renders a standard movie card without HTML code-block indentation errors."""
    mid = movie["movie_id"]
    title = movie["title"]
    year = movie.get("release_year") or "N/A"
    genres = movie.get("genres_list") or []
    rating = movie.get("avg_rating") or movie.get("score") or 4.0
    explanation = movie.get("explanation")
    is_cold = movie.get("is_cold_start", False) or mid == 9999 or "Space Heist" in title

    hue = (mid * 37) % 360
    badge_label = "COLD START" if is_cold else f"★ {rating:.1f}"
    genre_tags_html = "".join([f'<span class="genre-tag">{g}</span>' for g in genres[:3]])
    poster_url = get_movie_poster_url(mid, title)

    if poster_url:
        poster_html = f"""<div class="movie-card-poster-wrapper"><img src="{poster_url}" alt="{title}" class="movie-card-poster-img" loading="lazy" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" /><div class="movie-card-poster-fallback" style="display: none; background: linear-gradient(135deg, hsl({hue}, 40%, 12%) 0%, hsl({(hue+45)%360}, 50%, 18%) 100%);"><div class="movie-card-badge">{badge_label}</div><div class="poster-fallback-title">{title}</div><div class="poster-fallback-year">{year}</div></div><div class="movie-card-badge">{badge_label}</div></div>"""
    else:
        poster_html = f"""<div class="movie-card-poster-wrapper"><div class="movie-card-poster-fallback" style="display: flex; background: linear-gradient(135deg, hsl({hue}, 40%, 12%) 0%, hsl({(hue+45)%360}, 50%, 18%) 100%);"><div class="movie-card-badge">{badge_label}</div><div class="poster-fallback-title">{title}</div><div class="poster-fallback-year">{year}</div></div></div>"""

    card_html = f"""<div class="movie-card"><div>{poster_html}<div class="movie-card-title" title="{title}">{title}</div><div class="movie-card-meta"><span class="rating-pill">★ {rating:.1f}</span><span>•</span><span>{year}</span></div><div class="movie-card-genres">{genre_tags_html}</div></div></div>"""

    render_html(card_html)

    # Interactive Action Row (Watch Demo, Watchlist, Like, Dislike, Rate)
    in_wl = is_in_watchlist(user_id, mid)
    active_fb = get_feedback(user_id, mid)

    c_watch, c1, c2, c3, c4 = st.columns([1.3, 1.1, 0.8, 0.8, 1.0])

    with c_watch:
        if st.button("▶ Watch", key=f"{key_prefix}_watch_{mid}", help=f"Watch 15s+ Demo of {title}"):
            st.session_state["cinema_playing_movie"] = movie
            st.rerun()

    with c1:
        wl_label = "✓ Saved" if in_wl else "+ List"
        if st.button(wl_label, key=f"{key_prefix}_wl_{mid}", help="Toggle Watchlist"):
            if in_wl:
                remove_from_watchlist(user_id, mid)
            else:
                add_to_watchlist(user_id, mid)
            st.rerun()

    with c2:
        like_active = (active_fb == "like")
        like_label = "👍" if not like_active else "💚"
        if st.button(like_label, key=f"{key_prefix}_like_{mid}", help="Like recommendation"):
            if like_active:
                remove_feedback(user_id, mid)
            else:
                set_feedback(user_id, mid, "like")
            st.rerun()

    with c3:
        dislike_active = (active_fb == "dislike")
        dislike_label = "👎" if not dislike_active else "💔"
        if st.button(dislike_label, key=f"{key_prefix}_dis_{mid}", help="Dislike recommendation"):
            if dislike_active:
                remove_feedback(user_id, mid)
            else:
                set_feedback(user_id, mid, "dislike")
            st.rerun()

    with c4:
        with st.popover("Rate", help="Rate this movie"):
            st.caption(f"Rate '{title}'")
            score = st.slider("Rating", 0.5, 5.0, 4.0, 0.5, key=f"{key_prefix}_slider_{mid}")
            if st.button("Submit", key=f"{key_prefix}_rate_btn_{mid}"):
                rate_movie(user_id, mid, score)
                st.success(f"Rated {score}★")
                st.rerun()

    if show_explanation and explanation:
        reason_text = explanation.get("explanation") if isinstance(explanation, dict) else str(explanation)
        status_note = explanation.get("status_note") if isinstance(explanation, dict) else None
        with st.expander("Why this movie?", expanded=False):
            if status_note:
                st.info(status_note)
            render_html(f"""<div class="explanation-box"><b>Signal:</b> {reason_text}</div>""")


def render_attention_heatmap(attention_data: Dict[str, Any]):
    """Renders an interactive Plotly heatmap of Sequential Transformer attention weights."""
    if not attention_data or "attention_matrix" not in attention_data:
        return

    matrix = attention_data["attention_matrix"]
    titles = [t[:24] + "..." if len(t) > 24 else t for t in attention_data["sequence_titles"]]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=titles,
        y=titles,
        colorscale=[
            [0.0, "#090A12"],
            [0.3, "#2A1859"],
            [0.6, "#8C5CFF"],
            [0.85, "#B77BFF"],
            [1.0, "#40D9E8"]
        ],
        hoverongaps=False,
        hovertemplate="Query: %{y}<br>Attended: %{x}<br>Attention Weight: %{z:.3f}<extra></extra>"
    ))

    fig.update_layout(
        title={
            "text": "Transformer Self-Attention Heatmap (Model Signals, Not Proof of Causation)",
            "font": {"color": "#FFFFFF", "size": 14}
        },
        paper_bgcolor="#171625",
        plot_bgcolor="#171625",
        font={"color": "#A0A5BA", "size": 10},
        margin={"l": 40, "r": 20, "t": 40, "b": 60},
        height=380,
        xaxis={"tickangle": -45, "showgrid": False},
        yaxis={"autorange": "reversed", "showgrid": False}
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sidebar_navigation(current_user: Dict[str, Any]):
    """Renders the fixed left sidebar matching the second reference screenshot."""
    render_html("""
        <div class="sidebar-brand-wrapper">
            <div class="sidebar-logo-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                    <polygon points="5 3 19 12 5 21 5 3" fill="url(#sidebarPurplePlayGrad)"/>
                    <defs>
                        <linearGradient id="sidebarPurplePlayGrad" x1="5" y1="3" x2="19" y2="21" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#8B2CF5"/>
                            <stop offset="1" stop-color="#C026FF"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <div class="sidebar-brand-text">Cineverse</div>
        </div>
    """)

    sidebar_items = [
        ("Home", "🏠", "🏠 Home"),
        ("Profile", "👤", "👤 Profile"),
        ("My List", "📺", "📺 My List"),
        ("Watch History", "🕒", "🕒 Watch History"),
        ("AI Assistant", "✨", "✨ AI Assistant"),
        ("Mood Discovery", "🧭", "🧭 Mood Discovery"),
        ("Analytics", "📊", "📊 Analytics"),
        ("Settings", "⚙️", "⚙️ Settings"),
    ]
    if (
        st.session_state.get("admin_preview_unlocked")
        or st.session_state.get("is_admin")
        or current_user.get("user_type") == "admin"
        or current_user.get("is_admin")
    ):
        sidebar_items.append(("Admin Portal", "🛡️", "🛡️ Admin Portal"))

    current_sel = st.session_state.get("nav_selection", "🏠 Home")
    if current_sel in ["✦ AI Assistant"]:
        current_sel = "✨ AI Assistant"
    elif current_sel in ["⊞ Browse", "⊞ Browse Movies", "🔍 Discover Movies"]:
        current_sel = "🧭 Mood Discovery"
    elif current_sel in ["📊 Taste", "📊 Taste Profile"]:
        current_sel = "📊 Analytics"

    with st.container(key="sidebar_nav"):
        for label, icon, target in sidebar_items:
            is_active = (current_sel == target)
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {label}", key=f"sb_nav_{target}", type=btn_type, use_container_width=True):
                st.session_state["nav_selection"] = target
                st.rerun()

    render_html("""
        <div class="sidebar-ai-promo-card">
            <div class="sidebar-ai-star">★</div>
            <div class="sidebar-ai-title">Cineverse AI</div>
            <div class="sidebar-ai-subtitle">Your next story.<br/>Already remembered.</div>
            <div class="sidebar-ai-wave">
                <span></span><span></span><span></span><span></span>
                <span></span><span></span><span></span><span></span>
            </div>
        </div>
    """)

    render_html("<div style='height: 16px;'></div>")


@st.dialog("🎬 Cineverse Cinema Player", width="large")
def render_cinema_dialog(movie: Dict[str, Any], user_id: int):
    """Renders the fullscreen-style video demo player dialog for any movie."""
    mid = movie.get("movie_id") or movie.get("id") or 10001
    title = movie.get("title", "Featured Movie").split("(")[0].strip()
    year = movie.get("release_year") or ""
    genres = movie.get("genres_list") or []

    video_info = get_movie_video_info(mid, title, genres)
    video_url = video_info.get("video_url") or video_info.get("backup_mp4")
    backup_mp4 = video_info.get("backup_mp4") or "https://vjs.zencdn.net/v/oceans.mp4"
    badge = video_info.get("badge", "HD Demo Preview")
    duration = video_info.get("duration", "45s+ Preview")
    synopsis = video_info.get("synopsis", f"Experience the 15s+ video demo of {title} powered by Cineverse AI.")

    st.markdown(
        f"### 🎬 {title} <span style='font-size: 0.92rem; color: #40D9E8; font-weight: 600;'>[{badge} • {duration}]</span>",
        unsafe_allow_html=True
    )

    # High-Definition 15s+ Video Player with Dual-Stream Assurance
    if video_url and backup_mp4 and video_url != backup_mp4:
        v_tab1, v_tab2 = st.tabs(["▶ Official Demo Trailer", "⚡ Instant Direct Stream"])
        with v_tab1:
            st.video(video_url)
        with v_tab2:
            st.video(backup_mp4)
    else:
        st.video(video_url or backup_mp4)

    c_syn, c_act = st.columns([2.5, 1.5])
    with c_syn:
        st.caption(synopsis)
        if genres:
            st.markdown(f"**Genres:** {' • '.join(genres[:4])}")
    with c_act:
        in_wl = is_in_watchlist(user_id, mid)
        wl_label = "✓ In My List" if in_wl else "+ Add to My List"
        if st.button(wl_label, key=f"dialog_wl_btn_{mid}", use_container_width=True):
            if in_wl:
                remove_from_watchlist(user_id, mid)
            else:
                add_to_watchlist(user_id, mid)
            st.rerun()


@st.dialog("🎬 Movie Details & Intelligence", width="large")
def render_movie_details_dialog(movie: Dict[str, Any], user_id: int):
    """Renders the comprehensive movie details and synopsis modal."""
    mid = movie.get("movie_id") or movie.get("id") or 10001
    title = movie.get("title", "Featured Film").split("(")[0].strip()
    year = movie.get("release_year") or "2024"
    genres = movie.get("genres_list") or []
    rating = movie.get("avg_rating") or 4.5
    
    video_info = get_movie_video_info(mid, title, genres)
    synopsis = video_info.get("synopsis", f"{title} is a landmark cinematic experience curated by Cineverse AI.")
    badge = video_info.get("badge", "Recommended Feature")
    duration = video_info.get("duration", "Full Length Feature")
    
    poster_url = get_movie_poster_url(mid, title)
    if not poster_url:
        poster_url = "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"
        
    c_img, c_info = st.columns([1, 2.2], gap="medium")
    with c_img:
        st.image(poster_url, use_container_width=True)
    with c_info:
        st.markdown(f"## {title} <span style='font-size: 1.1rem; color: #B77BFF;'>({year})</span>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='display: flex; gap: 8px; align-items: center; margin-bottom: 14px; flex-wrap: wrap;'>"
            f"<span style='color: #FFD500; font-weight: 700; background: rgba(255,213,0,0.15); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(255,213,0,0.3);'>★ {rating:.1f}</span>"
            f"<span style='color: #40D9E8; font-weight: 600; background: rgba(64,217,232,0.12); padding: 3px 10px; border-radius: 6px;'>{duration}</span>"
            f"<span style='color: #E2B5FF; font-weight: 600; background: rgba(157,68,247,0.22); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(192,38,255,0.4);'>★ {badge}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        if genres:
            st.markdown(f"**Genres:** {' • '.join(genres)}")
        st.markdown(f"**Synopsis:**\n\n{synopsis}")
        
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("▶ Watch Trailer Demo", key=f"details_play_btn_{mid}", type="primary", use_container_width=True):
                st.session_state["cinema_playing_movie"] = movie
                st.rerun()
        with b2:
            in_wl = is_in_watchlist(user_id, mid)
            wl_label = "✓ In My List" if in_wl else "+ Add to My List"
            if st.button(wl_label, key=f"details_wl_btn_{mid}", use_container_width=True):
                if in_wl:
                    remove_from_watchlist(user_id, mid)
                else:
                    add_to_watchlist(user_id, mid)
                st.rerun()
