"""For You Page for Cineverse AI."""

import streamlit as st
from ui.components import (
    render_hero,
    render_section_header,
    render_movie_card,
    render_attention_heatmap,
    render_html
)
from services.recommendation_service import get_recommendation_service
from services.model_service import get_model_registry
from services.cold_start_service import get_cold_start_engine


def render_for_you_page(user: dict):
    user_id = user["user_id"]
    display_name = user.get("display_name") or user["username"]

    render_hero(
        title="Personalized Recommendations",
        subtitle="Compare three recommendation algorithms with real-time model telemetry, self-attention maps, and cold-start metadata projections.",
        user_name=display_name
    )

    rec_service = get_recommendation_service()
    registry = get_model_registry()

    # Model Selector Control Bar
    col_algo, col_count, col_kill = st.columns([2.5, 1, 1.5])

    with col_algo:
        algo_options = [
            "Automatic Best Model",
            "Sequential Transformer",
            "Matrix Factorization",
            "Weighted Popularity",
            "Cold-Start Metadata Matching"
        ]
        selected_algo = st.selectbox(
            "Select Recommendation Engine",
            options=algo_options,
            index=algo_options.index(st.session_state.get("selected_algorithm", "Automatic Best Model")),
            key="for_you_algo_select",
            help="Choose between Bayesian Popularity, Matrix Factorization, Transformer, or Cold-Start Metadata"
        )
        st.session_state["selected_algorithm"] = selected_algo

    with col_count:
        num_recs = st.number_input("Limit", min_value=4, max_value=20, value=8, step=4, key="for_you_limit")

    with col_kill:
        # Reliability Kill Switch / Restore Controls
        tr_status = registry.get_transformer_status()
        st.caption("Reliability Failover")
        if tr_status["healthy"]:
            if st.button("💥 Kill Transformer", key="kill_tr_btn", help="Simulate Transformer crash to verify automatic fallback"):
                registry.kill_transformer("Manually triggered failure demo")
                st.toast("Sequential Transformer disabled. Fallback system active!", icon="⚠️")
                st.rerun()
        else:
            if st.button("🔄 Restore Transformer", key="restore_tr_btn", help="Restore Sequential Transformer to operational state"):
                registry.restore_transformer()
                st.toast("Sequential Transformer restored to operational!", icon="✅")
                st.rerun()

    # Fetch Recommendations
    res = rec_service.get_recommendations(
        user_id=user_id,
        algorithm=selected_algo,
        limit=num_recs
    )

    # Telemetry and Status Banner
    render_html(f"""
        <div style="background: rgba(23, 22, 37, 0.9); border: 1px solid rgba(140, 92, 255, 0.2); border-radius: 10px; padding: 12px 18px; margin: 16px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 0.82rem; color: #A0A5BA;">ACTIVE ENGINE:</span>
                <span style="font-size: 0.95rem; font-weight: 700; color: #40D9E8;">{res['algorithm']}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span style="font-size: 0.82rem; color: #A0A5BA;">MEASURED LATENCY:</span>
                <span style="font-size: 0.95rem; font-weight: 700; color: #FFEE00;">{res['latency_ms']} ms</span>
            </div>
        </div>
    """)

    # Fallback Alert if applicable
    if res.get("fallback_used"):
        render_html(f"""
            <div class="fallback-alert">
                <span style="font-size: 1.4rem;">🚨</span>
                <div>
                    <b>Automatic Fallback Engaged!</b><br/>
                    The requested engine was unavailable ({res['fallback_reason']}). Cineverse seamlessly switched to <b>Weighted Popularity</b> to ensure uninterrupted user experience.
                </div>
            </div>
        """)

    # 1. Main Recommendation Grid
    recs = res.get("recommendations", [])
    if recs:
        render_section_header(
            f"Tailored Selection for {display_name}",
            f"{len(recs)} suggestions with model-signal explanations",
            icon="🎬"
        )
        grid_cols = st.columns(4)
        for i, m in enumerate(recs):
            with grid_cols[i % 4]:
                render_movie_card(m, user_id=user_id, show_explanation=True, key_prefix=f"fy_{i}")

    # 2. Sequential Transformer Attention Heatmap
    if res.get("attention_data"):
        render_section_header("Sequential Transformer Attention Visualization", "Real model self-attention signals over your watch sequence", icon="🧠")
        st.caption("Label Notice: Model attention signals indicate token representation weighting inside the PyTorch MultiheadAttention layer; they represent statistical association, not proof of causation.")
        render_attention_heatmap(res["attention_data"])

    # 3. Cold-Start Demonstration Section
    render_section_header("Cold-Start Strategy Demonstration", "Recommending new items with 0 interaction history", icon="🚀")
    render_html("""
        <div style="font-size: 0.85rem; color: #A0A5BA; margin-bottom: 12px; line-height: 1.5;">
            In collaborative filtering, new movies suffer from the <b>Cold-Start Problem</b> because no user has rated them yet.
            Cineverse overcomes this by constructing <b>hybrid metadata embeddings</b> blending Genre vectors, Title tokens, and Release Year.
            Below is our unrated test film <b>"Space Heist 2026"</b> matched via metadata similarity:
        </div>
    """)

    cold_engine = get_cold_start_engine()
    cold_demo = cold_engine.recommend_cold_start(user_id=user_id, limit=4, force_include_demo=True)
    c_cols = st.columns(4)
    for i, cm in enumerate(cold_demo[:4]):
        with c_cols[i % 4]:
            render_movie_card(cm, user_id=user_id, show_explanation=True, key_prefix=f"cs_demo_{i}")
