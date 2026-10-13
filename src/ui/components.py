"""Reusable UI component renderers for InsightFlow AI SaaS platform (Blue and White Theme)."""
from typing import List, Dict, Any, Optional, Callable
import streamlit as st
import pandas as pd
from src.data.profiler import ProfileReport
from src.data.cleaner import CleaningHistory
from src.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_DARK_BLUE,
    COLOR_LIGHT_BLUE, COLOR_PALE_BLUE, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_ERROR
)


def render_page_header(title: str, subtitle: str, badge: Optional[str] = None):
    """Render crisp, non-oversized SaaS page header with title, subtitle, and optional status badge."""
    badge_html = f'<div class="page-header-badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="page-header-box">
            <div class="page-header-left">
                <h1 class="page-title">{title}</h1>
                <div class="page-subtitle">{subtitle}</div>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_brand_header(title: str = "InsightFlow AI", subtitle: str = "Autonomous Data Analyst Agent"):
    """Render top brand hero banner matching the blue SaaS palette."""
    render_page_header(title, subtitle)


def render_dataset_info_bar(file_name: str, row_count: int, col_count: int, active_sheet: Optional[str] = None):
    """Render compact dataset info bar beneath page header."""
    sheet_info = f" • Sheet: <b>{active_sheet}</b>" if active_sheet else ""
    st.markdown(
        f"""
        <div class="dataset-info-bar">
            <div class="dataset-info-left">
                <span class="dataset-info-filename">📁 {file_name}</span>
                <span class="dataset-info-meta">📊 {row_count:,} Rows × {col_count} Columns{sheet_info}</span>
            </div>
            <div class="dataset-info-meta" style="color: {COLOR_PRIMARY}; font-weight: 500;">
                ● Active Dataset Loaded
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpis(profile: ProfileReport):
    """Render row of top dataset health KPI cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Records</div>
                <div class="kpi-value">{profile.row_count:,}</div>
                <div class="kpi-sub">Rows Analyzed</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Dimensions</div>
                <div class="kpi-value">{profile.column_count}</div>
                <div class="kpi-sub">{len(profile.numerical_columns)} Num • {len(profile.categorical_columns)} Cat</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        completeness = round(100.0 - profile.missing_pct, 1)
        sub_color = COLOR_SUCCESS if profile.missing_pct == 0 else COLOR_WARNING
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Data Density</div>
                <div class="kpi-value">{completeness}%</div>
                <div class="kpi-sub" style="color: {sub_color};">{profile.missing_cells:,} Null Cells</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        dup_color = COLOR_SUCCESS if profile.duplicate_rows == 0 else COLOR_ERROR
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Duplicates</div>
                <div class="kpi-value">{profile.duplicate_rows:,}</div>
                <div class="kpi-sub" style="color: {dup_color};">{profile.duplicate_pct}% Duplicate Rate</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        target_display = f"`{profile.potential_targets[0]}`" if profile.potential_targets else "None"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Primary Target</div>
                <div class="kpi-value" style="font-size: 1.15rem; word-break: break-all;">{target_display}</div>
                <div class="kpi-sub">{len(profile.potential_targets)} Candidates Detected</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_chat_welcome():
    """Render ChatGPT-style welcome hero with prompt cards."""
    st.markdown(
        """
        <div class="chat-welcome-container">
            <div class="chat-welcome-title">What would you like to discover in your data?</div>
            <div class="chat-welcome-subtitle">Ask questions in natural language, calculate KPIs, generate charts, or predict future trends.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_default_prompt_cards(profile: Optional[ProfileReport]) -> List[Dict[str, str]]:
    """Return 4-6 contextual prompt cards for the ChatGPT welcome screen."""
    cards = []
    num_cols = profile.numerical_columns if profile else []
    cat_cols = profile.categorical_columns if profile else []
    dt_cols = profile.datetime_columns if profile else []

    if num_cols:
        cards.append({
            "icon": "💰",
            "prompt": f"What is the total {num_cols[0]}?",
            "title": f"Calculate {num_cols[0]}",
            "desc": "Compute aggregate sum and statistical summary"
        })

    if cat_cols and num_cols:
        cards.append({
            "icon": "🏆",
            "prompt": f"Which {cat_cols[0]} has the highest {num_cols[0]}?",
            "title": f"Top Performing {cat_cols[0]}",
            "desc": f"Rank categories by {num_cols[0]}"
        })
        cards.append({
            "icon": "📊",
            "prompt": f"Create a graph of {num_cols[0]} by {cat_cols[0]}",
            "title": "Visualize Breakdown",
            "desc": "Generate interactive comparison chart"
        })

    if dt_cols and num_cols:
        cards.append({
            "icon": "🔮",
            "prompt": f"Forecast {num_cols[0]} for the next 30 days",
            "title": "Time-Series Forecast",
            "desc": "Predict 30-day trajectory with 95% confidence bounds"
        })

    cards.append({
        "icon": "💡",
        "prompt": "Recommend actions to improve profitability and performance",
        "title": "Strategic Recommendations",
        "desc": "Synthesize data-backed opportunities and risk factors"
    })

    cards.append({
        "icon": "🔍",
        "prompt": "Identify missing values and outliers",
        "title": "Data Hygiene Audit",
        "desc": "Detect null distributions and statistical anomalies"
    })

    return cards[:4]


def get_follow_up_action_chips(last_query: str, profile: Optional[ProfileReport]) -> List[Dict[str, str]]:
    """Return 3-4 dynamic follow-up action chips based on the previous query."""
    num_cols = profile.numerical_columns if profile else []
    cat_cols = profile.categorical_columns if profile else []
    dt_cols = profile.datetime_columns if profile else []
    q_lower = (last_query or "").lower()

    chips = []
    if "chart" in q_lower or "graph" in q_lower or "visual" in q_lower:
        if num_cols:
            chips.append({"label": f"🔍 Detect Anomalies in {num_cols[0]}", "query": f"Detect outliers and anomalies in {num_cols[0]}"})
            if dt_cols:
                chips.append({"label": f"🔮 Forecast {num_cols[0]}", "query": f"Forecast {num_cols[0]} for next 30 days"})
        if cat_cols and num_cols:
            chips.append({"label": f"🏆 Top 5 {cat_cols[0]} by {num_cols[0]}", "query": f"Which {cat_cols[0]} has the highest {num_cols[0]}?"})
        chips.append({"label": "💡 Strategic Actions", "query": "Recommend actions to improve profitability and performance"})
    elif "forecast" in q_lower or "predict" in q_lower:
        if num_cols:
            chips.append({"label": f"🔍 Analyze Outliers in {num_cols[0]}", "query": f"Detect outliers and anomalies in {num_cols[0]}"})
            chips.append({"label": f"📊 Distribution of {num_cols[0]}", "query": f"Show the distribution of {num_cols[0]}"})
        chips.append({"label": "💡 Risk & Opportunity Factors", "query": "Recommend actions to improve performance and minimize risks"})
    elif "outlier" in q_lower or "anomal" in q_lower:
        if num_cols and cat_cols:
            chips.append({"label": f"📊 Breakdown by {cat_cols[0]}", "query": f"Create a graph of {num_cols[0]} by {cat_cols[0]}"})
        if num_cols and dt_cols:
            chips.append({"label": f"🔮 Forecast {num_cols[0]}", "query": f"Forecast {num_cols[0]} for next 30 days"})
        chips.append({"label": "💡 Recommended Action Plan", "query": "Recommend actions based on discovered anomalies"})
    else:
        # Default follow-ups
        if cat_cols and num_cols:
            chips.append({"label": f"📊 Chart {num_cols[0]} by {cat_cols[0]}", "query": f"Create a graph of {num_cols[0]} by {cat_cols[0]}"})
        if num_cols and dt_cols:
            chips.append({"label": f"🔮 Forecast {num_cols[0]} (30D)", "query": f"Forecast {num_cols[0]} for next 30 days"})
        if num_cols:
            chips.append({"label": f"🔍 Outliers in {num_cols[0]}", "query": f"Detect outliers and anomalies in {num_cols[0]}"})
        chips.append({"label": "💡 Strategic Recommendations", "query": "Recommend actions to improve performance and efficiency"})

    return chips[:4]


def render_aha_ticker(insights: List[Dict[str, Any]], key_prefix: str = "aha") -> Optional[str]:
    """Render proactive insights ticker cards with 'Explore in Chat' triggers."""
    clicked_query = None
    for idx, insight in enumerate(insights):
        badge = insight.get("badge", "Discovery")
        title = insight.get("title", "Key Pattern")
        desc = insight.get("description", "")
        query = insight.get("query", "")

        st.markdown(
            f"""
            <div class="aha-ticker-card">
                <div class="aha-ticker-header">
                    <span class="aha-ticker-title">{title}</span>
                    <span class="aha-ticker-badge">{badge}</span>
                </div>
                <div class="aha-ticker-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        c_left, c_btn = st.columns([4, 1])
        with c_btn:
            if st.button("Explore 💬", key=f"{key_prefix}_btn_{idx}", help=f"Ask: {query}"):
                clicked_query = query

    return clicked_query
