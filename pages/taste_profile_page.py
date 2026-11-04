"""User Taste Profile Page for Cineverse AI."""

import streamlit as st
import plotly.graph_objects as go
from ui.components import render_hero, render_section_header, render_html
from services.user_service import get_user_taste_profile, get_user_stats


def render_taste_profile_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    render_hero(
        title="Your Taste Profile",
        subtitle="A deep look into your cinematic DNA, favorite genres, rating distributions, and era preferences.",
        user_name=display_name
    )

    stats = get_user_stats(user_id)
    profile = get_user_taste_profile(user_id)

    # 1. Top Level Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Total Ratings</div>
                <div class="metric-value">{stats['ratings_count']}</div>
                <div class="metric-delta">Verified entries</div>
            </div>
        """)
    with m2:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{stats['average_rating']} ★</div>
                <div class="metric-delta">Across all reviews</div>
            </div>
        """)
    with m3:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Watchlist Queue</div>
                <div class="metric-value">{stats['watchlist_count']}</div>
                <div class="metric-delta">Saved for later</div>
            </div>
        """)
    with m4:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Favorite Era</div>
                <div class="metric-value" style="font-size: 1.4rem; padding-top: 6px;">{profile.get('favorite_era', 'Modern')}</div>
                <div class="metric-delta">Highest frequency</div>
            </div>
        """)

    # 2. Taste Profile Persona Summary
    render_html(f"""
        <div style="background: linear-gradient(135deg, rgba(140, 92, 255, 0.12) 0%, rgba(64, 217, 232, 0.08) 100%); border: 1px solid rgba(140, 92, 255, 0.25); border-radius: 12px; padding: 20px 24px; margin: 24px 0;">
            <div style="font-size: 0.8rem; color: #40D9E8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">Taste Synthesis</div>
            <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin: 6px 0 8px 0;">{profile.get('taste_summary', '')}</div>
            <div style="font-size: 0.82rem; color: #A0A5BA;">
                Top Genre Preferences: <b style="color: #D8C5FF;">{', '.join(profile.get('top_genres', []))}</b>
            </div>
        </div>
    """)

    # 3. Interactive Charts (Rating Distribution & Genre Breakdown)
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        render_section_header("Rating Distribution", "How you distribute stars", icon="⭐")
        dist = profile.get("rating_distribution", {})
        stars = [1, 2, 3, 4, 5]
        counts = [dist.get(s, 0) for s in stars]

        fig_dist = go.Figure(go.Bar(
            x=[f"{s} Star" for s in stars],
            y=counts,
            marker={
                "color": ["#EF4444", "#F59E0B", "#10B981", "#8C5CFF", "#40D9E8"],
                "line": {"color": "rgba(255,255,255,0.1)", "width": 1}
            },
            text=counts,
            textposition="auto"
        ))
        fig_dist.update_layout(
            paper_bgcolor="#171625",
            plot_bgcolor="#171625",
            font={"color": "#A0A5BA"},
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            height=280,
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.06)"}
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with c_chart2:
        render_section_header("Genre Affinity Breakdown", "Relative composition of your watched films", icon="📊")
        g_data = profile.get("genre_profile", [])[:8]
        if g_data:
            g_labels = [g["genre"] for g in g_data]
            g_values = [g["count"] for g in g_data]

            fig_donut = go.Figure(go.Pie(
                labels=g_labels,
                values=g_values,
                hole=0.55,
                marker={
                    "colors": ["#8C5CFF", "#B77BFF", "#40D9E8", "#38BDF8", "#34D399", "#FBBF24", "#F87171", "#A78BFA"],
                    "line": {"color": "#171625", "width": 2}
                },
                textinfo="label+percent",
                hoverinfo="label+value+percent"
            ))
            fig_donut.update_layout(
                paper_bgcolor="#171625",
                plot_bgcolor="#171625",
                font={"color": "#FFFFFF", "size": 11},
                margin={"l": 10, "r": 10, "t": 10, "b": 10},
                height=280,
                showlegend=False
            )
            st.plotly_chart(fig_donut, use_container_width=True)
