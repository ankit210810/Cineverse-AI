"""Cineverse AI — Complete AI-Powered Movie Recommendation Platform.

Tagline: "Your next story. Already remembered."
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Page configuration - Set initial state to collapsed for full cinematic widescreen
st.set_page_config(
    page_title="Cineverse AI — Your next story. Already remembered.",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load and inject custom CSS
STYLE_PATH = PROJECT_DIR / "assets" / "style.css"
CURSOR_PATH = PROJECT_DIR / "assets" / "cursor.html"

if STYLE_PATH.exists():
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Force-reload dynamic UI modules so Streamlit doesn't cache stale modules in sys.modules
import importlib
for mod_name in ["ui.components", "ui.movie_carousel", "ui.hero_slider"]:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])

# Import services & components
from services.user_service import get_user, ensure_admin_user
from services.model_service import get_model_registry
from services.supabase_service import is_supabase_configured, sign_out
from ui.components import (
    render_logo,
    render_html,
    render_top_bar,
    render_duckshow_navbar,
    render_cinema_dialog,
    render_movie_details_dialog
)
from ui.voice_assistant import render_floating_ai_widget

# Import page modules
from pages.home_page import render_home_page
from pages.profile_page import render_profile_page
from pages.discover_page import render_discover_page
from pages.for_you_page import render_for_you_page
from pages.assistant_page import render_assistant_page
from pages.history_page import render_history_page
from pages.watchlist_page import render_watchlist_page
from pages.taste_profile_page import render_taste_profile_page
from pages.analytics_page import render_analytics_page
from pages.settings_page import render_settings_page
from pages.auth_page import render_auth_modal
from pages.admin_page import render_admin_page

# Session State Initialization — Default to Administrator Account (Ankit Kumar)
admin_account = ensure_admin_user("ankitkumar2009ara@gmail.com", "Ankit Kumar")
if "active_user_id" not in st.session_state:
    st.session_state["active_user_id"] = admin_account["user_id"]
    st.session_state["is_admin"] = True
    st.session_state["admin_preview_unlocked"] = True

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = True
if "admin_preview_unlocked" not in st.session_state:
    st.session_state["admin_preview_unlocked"] = True

if "selected_algorithm" not in st.session_state:
    st.session_state["selected_algorithm"] = "Automatic Best Model"

# Direct Navigation Query Parameter Handler (from floating AI pill or top nav links)
if "nav" in st.query_params:
    target_nav = st.query_params.get("nav")
    nav_map = {
        "ai": "✨ AI Assistant",
        "home": "🏠 Home",
        "series": "🎬 Series",
        "movies": "📽️ Movies",
        "anime": "🎌 Anime",
        "new_hot": "🔥 New & Hot",
        "my_list": "📺 My List",
        "admin": "🛡️ Admin Portal",
        "profile": "👤 Profile",
        "settings": "⚙️ Settings",
    }
    if target_nav in nav_map:
        st.session_state["nav_selection"] = nav_map[target_nav]
    st.query_params.clear()

# Direct Hero & Cinema Video Demo Player Trigger
if "play" in st.query_params:
    play_raw = st.query_params.get("play", "10003")
    if play_raw == "hero":
        play_mid = 10003
    else:
        try:
            play_mid = int(play_raw)
        except:
            play_mid = 10003
    from services.movie_service import get_movie
    m_play = get_movie(play_mid)
    if not m_play:
        m_play = {"movie_id": play_mid, "title": f"Featured Film #{play_mid}", "release_year": 2014}
    st.session_state["cinema_playing_movie"] = m_play
    st.query_params.clear()

# Direct Movie Details & Overview Modal Trigger
if "info" in st.query_params:
    info_raw = st.query_params.get("info", "10003")
    try:
        info_mid = int(info_raw)
    except:
        info_mid = 10003
    from services.movie_service import get_movie
    m_info = get_movie(info_mid)
    if not m_info:
        m_info = {"movie_id": info_mid, "title": f"Featured Film #{info_mid}", "release_year": 2014}
    st.session_state["info_viewing_movie"] = m_info
    st.query_params.clear()

if "nav_selection" not in st.session_state:
    st.session_state["nav_selection"] = "🏠 Home"

current_user = get_user(st.session_state["active_user_id"])
if not current_user:
    current_user = {"user_id": 42, "username": "movielens_user_42", "display_name": "MovieLens User 42"}

# Check if authenticated via Supabase
supabase_user = st.session_state.get("supabase_user")
if supabase_user:
    current_user["display_name"] = supabase_user.user_metadata.get("display_name") or supabase_user.email.split("@")[0]
    current_user["username"] = supabase_user.email

# Direct Watchlist Toggle Trigger
if "toggle_wl" in st.query_params:
    try:
        twl_mid = int(st.query_params.get("toggle_wl", 0))
        from services.feedback_service import is_in_watchlist, add_to_watchlist, remove_from_watchlist
        uid = current_user.get("user_id", 42)
        if is_in_watchlist(uid, twl_mid):
            remove_from_watchlist(uid, twl_mid)
        else:
            add_to_watchlist(uid, twl_mid)
    except Exception:
        pass
    st.query_params.clear()

registry = get_model_registry()

# -------------------------------------------------------------
# DUCKSHOW TOP HORIZONTAL NAVBAR (PINNED FLUSH AT TOP VIEWPORT)
# -------------------------------------------------------------
render_duckshow_navbar(current_user)

# Check if cinema player demo is requested
cinema_req = st.session_state.pop("cinema_playing_movie", None)
if cinema_req:
    render_cinema_dialog(cinema_req, current_user["user_id"])

# Check if movie info modal is requested
info_req = st.session_state.pop("info_viewing_movie", None)
if info_req:
    render_movie_details_dialog(info_req, current_user["user_id"])

# -------------------------------------------------------------
# MAIN CONTENT ROUTING
# -------------------------------------------------------------
active_page = st.session_state.get("nav_selection", "🏠 Home")

if active_page in ["🏠 Home", "Home"]:
    render_home_page(current_user)

elif active_page in ["🎬 Series", "Series"]:
    st.session_state["catalog_genre_filter"] = "Adventure"
    render_discover_page(current_user)

elif active_page in ["📽️ Movies", "Movies", "⊞ Browse Movies"]:
    st.session_state["catalog_genre_filter"] = "All"
    render_discover_page(current_user)

elif active_page in ["🎌 Anime", "Anime"]:
    st.session_state["catalog_genre_filter"] = "Animation"
    render_discover_page(current_user)

elif active_page in ["🔥 New & Hot", "New & Hot"]:
    render_for_you_page(current_user)

elif active_page in ["📺 My List", "My List", "🔖 My List"]:
    render_watchlist_page(current_user)

elif active_page in ["✨ AI Assistant", "AI Assistant", "✦ AI Assistant"]:
    render_assistant_page(current_user)

elif active_page in ["🧭 Mood Discovery", "Moods"]:
    render_discover_page(current_user)

elif active_page in ["📊 Analytics", "Analytics", "📈 Analytics"]:
    render_analytics_page(current_user)

elif active_page in ["🛡️ Admin", "🛡️ Admin Portal", "Admin"]:
    render_admin_page(current_user)

elif active_page in ["👤 Profile", "Profile"]:
    render_profile_page(current_user)

elif active_page in ["⚙️ Settings", "Settings"]:
    render_settings_page(current_user)

elif active_page in ["🔑 Account", "🔑 Sign In / Account"]:
    render_auth_modal()

# -------------------------------------------------------------
# PERSISTENT FLOATING AI VOICE COMPANION (DOCKED ON SIDE OF PAGE)
# -------------------------------------------------------------
render_floating_ai_widget(current_user)

# -------------------------------------------------------------
# ANIMATED CURSOR INJECTION (DOCKED AT BOTTOM TO ELIMINATE TOP GAP)
# -------------------------------------------------------------
if CURSOR_PATH.exists():
    with open(CURSOR_PATH, "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=0)
