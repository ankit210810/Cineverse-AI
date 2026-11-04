"""User Profile & Administrator Account Management for Cineverse AI."""

import streamlit as st
from ui.components import render_html
from database.db import get_db_connection
from services.user_service import get_user_stats, get_user_taste_profile
from services.feedback_service import get_watchlist, get_user_ratings


def render_profile_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or "Ankit Kumar"
    email = user.get("email") or user.get("username") or "ankitkumar2009ara@gmail.com"
    is_admin = user.get("user_type") == "admin" or user.get("is_admin", True) or st.session_state.get("is_admin", True)
    initial = display_name[0].upper() if display_name else "A"

    # Profile Hero Banner
    render_html(f"""
        <div class="profile-header-card">
            <div class="profile-avatar-large">{initial}</div>
            <div class="profile-meta-wrap">
                <div class="profile-badges-row">
                    <span class="profile-badge-admin">🛡️ Administrator</span>
                    <span class="profile-badge-vip">★ VIP Member</span>
                    <span class="profile-badge-verified">✓ Verified Account</span>
                </div>
                <div class="profile-name">{display_name}</div>
                <div class="profile-email">✉ {email}</div>
                <div class="profile-subtext">Cineverse AI Platform Administrator & Premium Cinephile</div>
            </div>
        </div>
    """)

    # Quick Action Bar
    a_col1, a_col2, a_col3, a_col4 = st.columns(4)
    with a_col1:
        if st.button("🛡️ Admin Portal", key="prof_btn_admin", use_container_width=True, type="primary"):
            st.session_state["nav_selection"] = "🛡️ Admin Portal"
            st.rerun()
    with a_col2:
        if st.button("📺 My Watchlist", key="prof_btn_wl", use_container_width=True):
            st.session_state["nav_selection"] = "📺 My List"
            st.rerun()
    with a_col3:
        if st.button("⚙️ Account Settings", key="prof_btn_settings", use_container_width=True):
            st.session_state["nav_selection"] = "⚙️ Settings"
            st.rerun()
    with a_col4:
        if st.button("🚪 Sign In / Switch Account", key="prof_btn_switch", use_container_width=True):
            st.session_state["nav_selection"] = "🔑 Sign In / Account"
            st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 4 Key Metrics Cards
    stats = get_user_stats(user_id)
    total_rated = stats.get("total_rated", 12)
    avg_rating = stats.get("average_rating", 4.5)
    watchlist_cnt = stats.get("watchlist_count", 8)
    history_cnt = stats.get("history_count", 24)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Watched Titles</div>
                <div class="metric-value" style="color: #FFFFFF;">{history_cnt}</div>
                <div class="metric-delta" style="color: #8B2CF5;">▶ 56 Total Hours</div>
            </div>
        """)
    with m2:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Average Rating</div>
                <div class="metric-value" style="color: #FFD500;">★ {avg_rating:.1f}</div>
                <div class="metric-delta" style="color: #9A9EBA;">Across {total_rated} Rated Titles</div>
            </div>
        """)
    with m3:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Saved to List</div>
                <div class="metric-value" style="color: #C026FF;">🔖 {watchlist_cnt}</div>
                <div class="metric-delta" style="color: #9A9EBA;">Queued to Watch</div>
            </div>
        """)
    with m4:
        render_html("""
            <div class="metric-card">
                <div class="metric-label">Security Tier</div>
                <div class="metric-value" style="color: #34D399;">ROOT</div>
                <div class="metric-delta" style="color: #34D399;">Full Administrator Privileges</div>
            </div>
        """)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Two Column Layout: Taste Analysis & Administrator Controls
    col_left, col_right = st.columns([1.3, 1.0], gap="large")

    with col_left:
        st.subheader("Personal Taste DNA & AI Profile")
        taste = get_user_taste_profile(user_id)
        top_genres = taste.get("top_genres", ["Sci-Fi", "Action", "Drama", "Adventure", "Thriller"])
        summary_text = taste.get("taste_summary") or "Passionate about mind-bending Sci-Fi, thought-provoking drama, and high-concept cinematic thrillers."

        render_html(f"""
            <div class="profile-content-box">
                <div style="font-size: 0.95rem; color: #E0AAFF; margin-bottom: 12px; line-height: 1.5;">
                    {summary_text}
                </div>
                <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: #9A9EBA; margin-bottom: 8px;">
                    Dominant Affinity Genres
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    {''.join(f'<span class="profile-genre-tag">{g}</span>' for g in top_genres)}
                </div>
                <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(139, 44, 245, 0.2); font-size: 0.85rem; color: #D8C5FF;">
                    <b>Primary Era:</b> 1990s & 2010s Modern Space Classics<br/>
                    <b>Sequential Transformer Signal:</b> Strongly influenced by <i>Interstellar</i>, <i>Inception</i>, and <i>The Matrix</i>
                </div>
            </div>
        """)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.subheader("Recently Rated by You")
        ratings_list = get_user_ratings(user_id, limit=5)
        if ratings_list:
            for r in ratings_list:
                render_html(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: rgba(14, 10, 32, 0.7); border: 1px solid rgba(139, 44, 245, 0.15); border-radius: 10px; margin-bottom: 8px;">
                        <span style="font-weight: 600; color: #FFFFFF;">{r['title']}</span>
                        <span style="color: #FFD500; font-weight: 700;">★ {r['rating']}</span>
                    </div>
                """)
        else:
            st.caption("No rated movies yet. Browse and rate titles to shape your recommendation engine!")

    with col_right:
        st.subheader("Administrator Controls & System Privileges")
        render_html("""
            <div class="profile-content-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="color: #9A9EBA; font-size: 0.85rem;">Account Authority</span>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.85rem;">● SUPERUSER</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="color: #9A9EBA; font-size: 0.85rem;">Transformer Engine</span>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.85rem;">● ACTIVE & SERVING</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="color: #9A9EBA; font-size: 0.85rem;">Matrix Factorization</span>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.85rem;">● LATENT FACTORS (32)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="color: #9A9EBA; font-size: 0.85rem;">Database Sync</span>
                    <span style="color: #34D399; font-weight: 700; font-size: 0.85rem;">● SQLITE + SUPABASE</span>
                </div>
            </div>
        """)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.subheader("Edit Profile Details")
        with st.form("edit_profile_form"):
            new_name = st.text_input("Display Name", value=display_name)
            new_email = st.text_input("Email", value=email, disabled=True, help="Contact administrator to change primary account email.")
            save_btn = st.form_submit_button("Save Profile Changes", use_container_width=True)
            if save_btn:
                if new_name.strip():
                    conn = get_db_connection()
                    try:
                        conn.execute("UPDATE users SET display_name = ? WHERE user_id = ?", (new_name.strip(), user_id))
                        conn.commit()
                        st.success("Profile updated successfully!")
                        st.rerun()
                    finally:
                        conn.close()
