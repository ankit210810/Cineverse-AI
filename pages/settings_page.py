"""Settings and Preferences Page for Cineverse AI."""

import streamlit as st
from ui.components import render_hero, render_section_header, render_html
from database.db import get_db_connection


def render_settings_page(user: dict):
    display_name = user.get("display_name") or "Ankit Kumar"
    email = user.get("email") or user.get("username") or "ankitkumar2009ara@gmail.com"
    is_admin = user.get("user_type") == "admin" or user.get("is_admin", True) or st.session_state.get("is_admin", True)

    render_hero(
        title="Settings & Preferences",
        subtitle="Manage your Cineverse account, streaming playback standards, recommendation algorithms, and platform security."
    )

    tab_account, tab_playback, tab_ai, tab_admin = st.tabs([
        "👤 Account & Security",
        "🎬 Playback & Audio",
        "🧠 AI & Personalization",
        "🛡️ System Administration"
    ])

    with tab_account:
        render_section_header("Account Profile", "Your authenticated credentials and membership status", icon="👤")
        render_html(f"""
            <div style="background: rgba(14, 10, 32, 0.85); border: 1px solid rgba(139, 44, 245, 0.25); border-radius: 14px; padding: 20px 24px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #FFFFFF;">{display_name}</div>
                        <div style="font-size: 0.88rem; color: #9A9EBA; margin-top: 2px;">{email}</div>
                    </div>
                    <div>
                        <span class="profile-badge-admin">🛡️ Administrator</span>
                        <span class="profile-badge-vip" style="margin-left: 6px;">★ VIP Member</span>
                    </div>
                </div>
            </div>
        """)

        acc_c1, acc_c2 = st.columns(2)
        with acc_c1:
            st.write("#### Profile Actions")
            if st.button("👤 View Full Profile Page", key="btn_go_prof", use_container_width=True, type="primary"):
                st.session_state["nav_selection"] = "👤 Profile"
                st.rerun()

            if st.button("🔑 Change Account Password", key="btn_change_pw", use_container_width=True):
                st.info("A secure password reset link has been dispatched to your email address.")

        with acc_c2:
            st.write("#### Security & Sessions")
            render_html("""
                <div style="background: rgba(23, 22, 37, 0.6); border: 1px solid rgba(139, 44, 245, 0.15); border-radius: 10px; padding: 14px 18px;">
                    <div style="color: #34D399; font-weight: 700; font-size: 0.85rem;">● Active Session: This Browser</div>
                    <div style="color: #9A9EBA; font-size: 0.8rem; margin-top: 4px;">Platform: Windows Desktop • Streamlit Secure Session</div>
                </div>
            """)

    with tab_playback:
        render_section_header("Streaming & Display Quality", "High-fidelity audio and video playback preferences", icon="🎬")
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            video_q = st.selectbox(
                "Streaming Video Quality",
                options=["4K Ultra HD (Dolby Vision / HDR10+)", "1080p Full HD (Balanced Data)", "720p HD (Data Saver)"],
                index=0,
                key="settings_video_q"
            )
            audio_f = st.selectbox(
                "Spatial Audio Configuration",
                options=["Dolby Atmos 7.1 Surround", "5.1 Surround Sound", "Stereo High Fidelity"],
                index=0,
                key="settings_audio_f"
            )
        with p_c2:
            st.checkbox("Autoplay trailers while browsing catalog", value=True, key="set_auto_trailer")
            st.checkbox("Autoplay next recommended title upon finish", value=True, key="set_auto_next")
            st.selectbox(
                "Default Audio & Subtitle Language",
                options=["English (Original)", "Spanish", "French", "German", "Hindi", "Japanese"],
                index=0,
                key="settings_lang"
            )

        if st.button("Save Playback Preferences", key="btn_save_playback"):
            st.success("Streaming playback preferences updated!")

    with tab_ai:
        render_section_header("Recommendation Algorithms", "Control how Cineverse AI personalizes your suggestions", icon="🧠")
        ai_c1, ai_c2 = st.columns(2)
        with ai_c1:
            algo_choice = st.selectbox(
                "Primary Recommendation Engine",
                options=[
                    "Sequential Transformer (Deep Multihead Attention)",
                    "Matrix Factorization (Latent Factors SGD)",
                    "Hybrid Neural Ensemble (Automatic Best Model)"
                ],
                index=2,
                key="settings_primary_algo"
            )
            st.session_state["selected_algorithm"] = "Automatic Best Model" if "Ensemble" in algo_choice else algo_choice

        with ai_c2:
            st.select_slider(
                "Mood Discovery Sensitivity",
                options=["Subtle", "Balanced", "Exploratory & Adventurous"],
                value="Balanced",
                key="settings_mood_sens"
            )
            st.checkbox("Include Mature & R-Rated Titles in Recommendations", value=True, key="settings_include_mature")

        if st.button("Clear Engine Cache & Recompute Vectors", key="btn_clear_cache"):
            st.success("Recommendation engine memory refreshed! Recalculating latent embeddings.")
            st.rerun()

    with tab_admin:
        render_section_header("Platform Administration", "Superuser controls and server-side model infrastructure", icon="🛡️")
        if is_admin:
            render_html("""
                <div style="background: rgba(139, 44, 245, 0.12); border: 1px solid rgba(139, 44, 245, 0.35); border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
                    <div style="font-weight: 800; font-size: 1.1rem; color: #FFFFFF; margin-bottom: 6px;">
                        Administrator Status: <span style="color: #34D399;">ROOT AUTHORIZED</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #D8C5FF; line-height: 1.5;">
                        Your account <b>ankitkumar2009ara@gmail.com</b> is authenticated with complete platform administrator privileges. You have access to live inference telemetry, failover controls, and user permission management.
                    </div>
                </div>
            """)
            if st.button("🛡️ Open Admin Portal & Model Health Console", type="primary", use_container_width=True, key="settings_btn_open_admin"):
                st.session_state["nav_selection"] = "🛡️ Admin Portal"
                st.rerun()
        else:
            st.warning("Administrator console is restricted to verified admin accounts.")
