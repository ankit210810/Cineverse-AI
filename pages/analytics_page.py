"""Admin and Model Analytics Dashboard for Cineverse AI."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.components import render_hero, render_section_header, render_movie_card, render_html
from database.db import get_db_connection
from services.model_service import get_model_registry
from services.evaluation_service import get_or_create_evaluation, run_quick_evaluation
from services.cold_start_service import get_cold_start_engine


def render_analytics_page(user: dict):
    render_hero(
        title="Admin & Model Analytics",
        subtitle="Quantitative evaluation metrics (Recall@10, NDCG@10), system reliability controls, and live request latency telemetry."
    )

    registry = get_model_registry()

    # 1. System Overview Metrics
    conn = get_db_connection()
    try:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_movies = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        total_ratings = conn.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
        rec_requests = conn.execute("SELECT COUNT(*) FROM recommendation_logs").fetchone()[0]
    finally:
        conn.close()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Total Users</div>
                <div class="metric-value">{total_users:,}</div>
                <div class="metric-delta">Active DB Records</div>
            </div>
        """)
    with m2:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Total Movies</div>
                <div class="metric-value">{total_movies:,}</div>
                <div class="metric-delta">MovieLens + Cold Start</div>
            </div>
        """)
    with m3:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Total Ratings</div>
                <div class="metric-value">{total_ratings:,}</div>
                <div class="metric-delta">100k Benchmark Dataset</div>
            </div>
        """)
    with m4:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Recommendations Served</div>
                <div class="metric-value">{rec_requests:,}</div>
                <div class="metric-delta">Logged Transactions</div>
            </div>
        """)

    # 2. Model Status & Failure Simulation Controls
    render_section_header("Engine Status & Reliability Controls", "Mandatory hackathon failover testbed", icon="🛡️")

    tr_status = registry.get_transformer_status()
    c_stat1, c_stat2 = st.columns([3, 2])

    with c_stat1:
        render_html(f"""
            <div style="background: rgba(23, 22, 37, 0.9); border: 1px solid rgba(140, 92, 255, 0.2); border-radius: 12px; padding: 16px 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <b>Sequential Transformer Status:</b>
                    <span class="status-badge {'healthy' if tr_status['healthy'] else 'killed'}">{tr_status['badge']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #A0A5BA; margin-bottom: 12px;">{tr_status['reason']}</div>
                <div style="font-size: 0.82rem; color: #D8C5FF;">
                    <b>Fallback Guarantee:</b> When degraded, Cineverse automatically redirects recommendation inference to Bayesian Weighted Popularity without downtime.
                </div>
            </div>
        """)

    with c_stat2:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if tr_status["healthy"]:
            if st.button("💥 Kill Transformer (Simulate Failure)", key="admin_kill_tr", use_container_width=True):
                registry.kill_transformer("Killed via Admin Dashboard to test failover")
                st.toast("Transformer offline! Fallback engaged.", icon="⚠️")
                st.rerun()
        else:
            if st.button("🔄 Restore Transformer to Healthy", key="admin_restore_tr", use_container_width=True):
                registry.restore_transformer()
                st.toast("Transformer restored successfully!", icon="✅")
                st.rerun()

    # 3. Model Performance Comparison Table & Evaluation
    render_section_header("Model Evaluation Benchmark", "Recall@10 and NDCG@10 on hold-out interactions", icon="📊")

    eval_data = get_or_create_evaluation()
    benchmark_df = pd.DataFrame(eval_data.get("benchmark_comparison", []))

    col_bench, col_chart = st.columns([1.2, 1])

    with col_bench:
        if not benchmark_df.empty:
            display_cols = ["model_name", "recall@10", "ndcg@10", "latency_ms", "strengths"]
            st.dataframe(
                benchmark_df[display_cols],
                column_config={
                    "model_name": "Model Architecture",
                    "recall@10": st.column_config.NumberColumn("Recall@10", format="%.3f"),
                    "ndcg@10": st.column_config.NumberColumn("NDCG@10", format="%.3f"),
                    "latency_ms": st.column_config.NumberColumn("Avg Latency (ms)", format="%.1f"),
                    "strengths": "Architectural Advantage"
                },
                hide_index=True,
                use_container_width=True
            )

        if st.button("⚡ Recompute Fresh Evaluation Batch", key="recompute_eval_btn"):
            with st.spinner("Computing metrics across user test split..."):
                res = run_quick_evaluation(sample_size=30)
                st.success(f"Evaluation finished! Transformer Recall@10: {res['transformer']['recall@10']:.3f}, NDCG@10: {res['transformer']['ndcg@10']:.3f}")
                st.rerun()

    with col_chart:
        models = [b["model_name"] for b in eval_data.get("benchmark_comparison", [])]
        recalls = [b["recall@10"] for b in eval_data.get("benchmark_comparison", [])]
        ndcgs = [b["ndcg@10"] for b in eval_data.get("benchmark_comparison", [])]

        fig_eval = go.Figure()
        fig_eval.add_trace(go.Bar(
            name="Recall@10",
            x=models,
            y=recalls,
            marker_color="#8C5CFF"
        ))
        fig_eval.add_trace(go.Bar(
            name="NDCG@10",
            x=models,
            y=ndcgs,
            marker_color="#40D9E8"
        ))
        fig_eval.update_layout(
            barmode="group",
            paper_bgcolor="#171625",
            plot_bgcolor="#171625",
            font={"color": "#FFFFFF"},
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            height=300,
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.06)", "title": "Score (0.0 to 1.0)"}
        )
        st.plotly_chart(fig_eval, use_container_width=True)

    # 4. Latency Telemetry & Monitoring (p50, p95, p99)
    render_section_header("Request Latency Monitoring", "Engineering target: p99 < 20 ms", icon="⚡")
    lat_stats = registry.get_latency_stats()

    l1, l2, l3, l4 = st.columns(4)
    with l1:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">Average Latency</div>
                <div class="metric-value">{lat_stats['avg_ms']} ms</div>
                <div class="metric-delta">{lat_stats['count']} requests logged</div>
            </div>
        """)
    with l2:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">p50 (Median)</div>
                <div class="metric-value">{lat_stats['p50_ms']} ms</div>
                <div class="metric-delta">50th percentile</div>
            </div>
        """)
    with l3:
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">p95 Latency</div>
                <div class="metric-value">{lat_stats['p95_ms']} ms</div>
                <div class="metric-delta">95th percentile</div>
            </div>
        """)
    with l4:
        target_badge = "✅ Target Met" if lat_stats['target_met'] else "⚠️ Under Optimization"
        render_html(f"""
            <div class="metric-card">
                <div class="metric-label">p99 Latency</div>
                <div class="metric-value">{lat_stats['p99_ms']} ms</div>
                <div class="metric-delta" style="color: {'#34D399' if lat_stats['target_met'] else '#FBBF24'};">{target_badge} (&lt; 20ms)</div>
            </div>
        """)

    if registry.latency_records:
        rec_df = pd.DataFrame(registry.latency_records[-40:])
        fig_lat = go.Figure()
        fig_lat.add_trace(go.Scatter(
            x=rec_df["time_str"],
            y=rec_df["latency_ms"],
            mode="lines+markers",
            line={"color": "#40D9E8", "width": 2},
            marker={"size": 6, "color": "#FFEE00"},
            name="Latency (ms)"
        ))
        fig_lat.add_hline(y=20.0, line_dash="dash", line_color="#EF4444", annotation_text="p99 Engineering Goal (20ms)")
        fig_lat.update_layout(
            paper_bgcolor="#171625",
            plot_bgcolor="#171625",
            font={"color": "#A0A5BA"},
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            height=250,
            yaxis={"showgrid": True, "gridcolor": "rgba(255,255,255,0.06)", "title": "Latency (ms)"}
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    # 5. Cold-Start Live Experiment
    render_section_header("Cold-Start Strategy Audit", "Evaluating unrated test item 'Space Heist 2026'", icon="🧪")
    cold_engine = get_cold_start_engine()
    space_heist_feat = cold_engine.movie_features.get(9999)
    if space_heist_feat:
        render_html(f"""
            <div style="background: rgba(140, 92, 255, 0.08); border: 1px solid rgba(140, 92, 255, 0.25); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
                <b style="color: #40D9E8;">Test Movie:</b> {space_heist_feat['title']} ({space_heist_feat['year']})<br/>
                <b style="color: #D8C5FF;">Genres:</b> {', '.join(space_heist_feat['genres'])}<br/>
                <b style="color: #FFEE00;">Training Interaction Count:</b> 0 (Strictly zero ratings in MovieLens dataset)<br/>
                <span style="font-size: 0.8rem; color: #A0A5BA;">Method: Projected via hybrid normalized metadata cosine similarity with active user genre vectors.</span>
            </div>
        """)
