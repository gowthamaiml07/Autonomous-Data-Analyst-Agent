"""InsightFlow AI — Autonomous Data Analyst Agent
Premium SaaS Platform with Blue & White Theme and ChatGPT-Style Streaming Conversation Interface
"""
import io
import os
import sys
import time
import uuid
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="InsightFlow AI — Autonomous Data Analyst Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports
from src.config import (
    APP_TITLE, APP_SUBTITLE, VERSION,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_DARK_BLUE,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_GRADIENT_END,
    COLOR_LIGHT_BLUE, COLOR_PALE_BLUE, COLOR_MAIN_BG,
    COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_SUCCESS, COLOR_SUCCESS_BG,
    COLOR_WARNING, COLOR_ERROR,
    AVAILABLE_MODELS, DEFAULT_GROQ_MODEL, FAST_GROQ_MODEL, SAMPLE_DATA_DIR
)
from src.ui.styles import CUSTOM_CSS
from src.ui.components import (
    render_page_header, render_brand_header, render_dataset_info_bar,
    render_kpis, render_chat_welcome,
    get_default_prompt_cards, get_follow_up_action_chips, render_aha_ticker
)
from src.data.loader import DataLoader, LoadResult
from src.data.profiler import DataProfiler, ProfileReport
from src.data.cleaner import DataCleaner, CleaningHistory, SafeFormulaEvaluator
from src.data.exporter import DataExporter
from src.tools.calculator import DataCalculator
from src.tools.visualizer import DataVisualizer
from src.tools.predictor import DataPredictor
from src.tools.recommender import RecommendationEngine
from src.reports.pdf_generator import PDFReportGenerator
from src.agent.graph import AnalystAgent
from src.agent.llm import LLMClient

# Apply custom master design system
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -------------------------------------------------------------
# Session State Initialization & Multi-Conversation Management
# -------------------------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "cleaning_history" not in st.session_state:
    st.session_state.cleaning_history = None
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.environ.get("GROQ_API_KEY", "")
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            st.session_state.groq_api_key = st.secrets["GROQ_API_KEY"].strip()
    except Exception:
        pass
if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_GROQ_MODEL
if "active_sheet" not in st.session_state:
    st.session_state.active_sheet = None
if "excel_sheets" not in st.session_state:
    st.session_state.excel_sheets = []
if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None
if "recent_datasets" not in st.session_state:
    st.session_state.recent_datasets = {}

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "target_nav" not in st.session_state:
    st.session_state.target_nav = None
if "regression_model_res" not in st.session_state:
    st.session_state.regression_model_res = None
if "classification_model_res" not in st.session_state:
    st.session_state.classification_model_res = None

# Multi-conversation management
if "conversations" not in st.session_state:
    init_id = str(uuid.uuid4())[:8]
    st.session_state.conversations = {
        init_id: {
            "id": init_id,
            "title": "General Analysis",
            "created_at": datetime.now().strftime("%b %d, %H:%M"),
            "messages": []
        }
    }
    st.session_state.active_conv_id = init_id
if "active_conv_id" not in st.session_state:
    st.session_state.active_conv_id = list(st.session_state.conversations.keys())[0]


def get_active_messages() -> list:
    """Retrieve messages for the active conversation."""
    cid = st.session_state.active_conv_id
    if cid in st.session_state.conversations:
        return st.session_state.conversations[cid]["messages"]
    return []


def create_new_conversation(title: str = "New Analysis") -> str:
    """Create a new conversation session and set it active."""
    new_id = str(uuid.uuid4())[:8]
    st.session_state.conversations[new_id] = {
        "id": new_id,
        "title": title,
        "created_at": datetime.now().strftime("%b %d, %H:%M"),
        "messages": []
    }
    st.session_state.active_conv_id = new_id
    return new_id


def set_active_dataset(df: pd.DataFrame, file_name: str, sheets=None, active_sheet=None, excel_bytes=None):
    """Set active dataset and auto-update profiler, audit history, and recent list."""
    st.session_state.df = df
    st.session_state.file_name = file_name
    st.session_state.profile = DataProfiler.profile(df)
    st.session_state.cleaning_history = CleaningHistory(df)
    st.session_state.excel_sheets = sheets or []
    st.session_state.active_sheet = active_sheet
    if excel_bytes:
        st.session_state.excel_bytes = excel_bytes
    # Record in recent datasets dictionary
    st.session_state.recent_datasets[file_name] = {
        "name": file_name,
        "rows": len(df),
        "cols": len(df.columns),
        "sheet": active_sheet,
        "loaded_at": datetime.now().strftime("%H:%M")
    }


# Auto-load default sales sample if empty on initial startup
if st.session_state.df is None:
    sample_path = os.path.join(SAMPLE_DATA_DIR, "sales_data.csv")
    if os.path.exists(sample_path):
        load_res = DataLoader.load(sample_path)
        if load_res.success:
            set_active_dataset(load_res.df, "sales_data.csv")


# -------------------------------------------------------------
# Fixed/Collapsible Dark Navy Sidebar Navigation
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand-box">
            <h2 class="sidebar-brand-title">📊 {APP_TITLE}</h2>
            <div class="sidebar-brand-sub">{APP_SUBTITLE} • v{VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # New Chat / Analysis action
    if st.button("➕ New Chat / Analysis", use_container_width=True, type="primary"):
        create_new_conversation("Data Discovery")
        st.session_state.target_nav = "💬 Ask AI"
        st.rerun()

    st.markdown("---")

    # Authoritative 9-view navigation structure matching reference layout
    nav_options = [
        "🏠 Home",
        "📁 Data Workspace",
        "💬 Ask AI",
        "📊 Visualization Studio",
        "🧪 Data Lab",
        "🔮 Prediction & Insights",
        "📑 Reports & History",
        "⚙️ Settings / About",
        "📱 Mobile Ask AI"
    ]

    default_nav_idx = 0
    if st.session_state.target_nav in nav_options:
        default_nav_idx = nav_options.index(st.session_state.target_nav)
        st.session_state.target_nav = None

    navigation = st.radio(
        "Platform Navigation",
        nav_options,
        index=default_nav_idx
    )

    st.markdown("---")

    # Active dataset status card in sidebar
    if st.session_state.df is not None:
        sheet_text = f" • Sheet: `{st.session_state.active_sheet}`" if st.session_state.active_sheet else ""
        st.markdown(
            f"""
            <div class="sidebar-dataset-card">
                <div class="sidebar-dataset-title">Active Dataset</div>
                <div class="sidebar-dataset-name">{st.session_state.file_name}</div>
                <div class="sidebar-dataset-meta">{len(st.session_state.df):,} rows × {len(st.session_state.df.columns)} cols{sheet_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="sidebar-dataset-card">
                <div class="sidebar-dataset-title">Active Dataset</div>
                <div class="sidebar-dataset-name" style="color: #94A3B8;">No dataset loaded</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # LLM Connection Status Indicator
    has_key = LLMClient.is_available(st.session_state.groq_api_key)
    if has_key:
        st.markdown('<span class="status-badge-active">● Groq LLM Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">● Deterministic Mode (Offline)</span>', unsafe_allow_html=True)
        st.caption("Add Groq API Key in Settings for streaming synthesis.")

    # Recent Conversation Sessions list
    st.markdown("---")
    st.markdown("###### 🕒 Recent Conversations")
    for cid, cinfo in list(st.session_state.conversations.items())[-5:]:
        is_active = (cid == st.session_state.active_conv_id)
        c_title = cinfo["title"][:22]
        c_cols = st.columns([4, 1])
        with c_cols[0]:
            btn_label = f"{'🔹 ' if is_active else '💬 '}{c_title}"
            if st.button(btn_label, key=f"sel_conv_{cid}", use_container_width=True):
                st.session_state.active_conv_id = cid
                st.session_state.target_nav = "💬 Ask AI"
                st.rerun()
        with c_cols[1]:
            if len(st.session_state.conversations) > 1:
                if st.button("🗑️", key=f"del_conv_{cid}", help="Delete chat"):
                    del st.session_state.conversations[cid]
                    if st.session_state.active_conv_id == cid:
                        st.session_state.active_conv_id = list(st.session_state.conversations.keys())[0]
                    st.rerun()

    # Compact user profile area at bottom of sidebar matching reference
    st.markdown(
        """
        <div class="sidebar-user-footer">
            <div class="sidebar-user-avatar">👤</div>
            <div>
                <div class="sidebar-user-name">Analyst Workspace</div>
                <div class="sidebar-user-role">Enterprise Edition • Active</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =============================================================
# 1. HOME DASHBOARD
# =============================================================
if navigation == "🏠 Home":
    render_page_header("Home Dashboard", "Your data. Your questions. Clear answers.")

    # Main content: Upload card on the left, Quick Actions card beside it
    col_upload, col_actions = st.columns([1, 1], gap="medium")

    with col_upload:
        st.markdown(
            f"""
            <div class="white-content-card">
                <div style="font-size: 2rem; color: {COLOR_PRIMARY}; margin-bottom: 0.3rem;">☁️</div>
                <div class="content-card-title">Upload your CSV or Excel file</div>
                <div class="content-card-desc">Drag and drop or browse tabular data files to begin autonomous analysis.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        home_uploader = st.file_uploader(
            "Upload your CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="home_file_uploader",
            label_visibility="collapsed"
        )
        st.markdown(
            f"""
            <div style="font-size: 0.78rem; color: {COLOR_TEXT_SECONDARY}; margin: 0.2rem 0 0.8rem 0;">
                Supported formats: <b>CSV, XLSX, XLS</b> • Max file size: <b>100MB</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        if home_uploader is not None:
            bytes_data = home_uploader.getvalue()
            inspect_info = DataLoader.inspect_file(io.BytesIO(bytes_data), home_uploader.name)
            if inspect_info.get("error"):
                st.error(inspect_info["error"])
            elif inspect_info.get("is_excel"):
                sheets = inspect_info["sheets"]
                selected_sheet = st.selectbox("Select Excel Worksheet", sheets, index=0, key="home_sheet_select")
                if st.button("Upload File", type="primary", key="home_btn_load_excel", use_container_width=True):
                    load_res = DataLoader.load(io.BytesIO(bytes_data), home_uploader.name, sheet_name=selected_sheet)
                    if load_res.success:
                        set_active_dataset(load_res.df, home_uploader.name, sheets=sheets, active_sheet=selected_sheet, excel_bytes=bytes_data)
                        st.success(f"Worksheet '{selected_sheet}' loaded successfully!")
                        st.rerun()
            else:
                if st.button("Upload File", type="primary", key="home_btn_load_csv", use_container_width=True):
                    load_res = DataLoader.load(io.BytesIO(bytes_data), home_uploader.name)
                    if load_res.success:
                        set_active_dataset(load_res.df, home_uploader.name)
                        st.success("CSV loaded successfully!")
                        st.rerun()
        else:
            if st.button("Upload File", type="primary", key="home_btn_empty_up", use_container_width=True):
                st.info("Browse or drop a CSV or Excel file above to upload.")

    with col_actions:
        st.markdown(
            """
            <div class="white-content-card">
                <div class="content-card-title">⚡ Quick Actions</div>
                <div class="content-card-desc">Jump straight to core intelligence and analytics modules:</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick Actions in exact order: 1. Ask AI, 2. Visualizations, 3. Data Lab, 4. Prediction
        qa_col1, qa_col2 = st.columns(2)
        with qa_col1:
            st.markdown(
                """
                <div class="quick-action-card">
                    <div class="quick-action-icon">💬</div>
                    <div class="quick-action-title">Ask AI</div>
                    <div class="quick-action-desc">Conversational reasoning, calculations & charts.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Ask AI 💬", key="home_qa_ask", use_container_width=True):
                st.session_state.target_nav = "💬 Ask AI"
                st.rerun()

            st.markdown(
                """
                <div class="quick-action-card" style="margin-top: 0.8rem;">
                    <div class="quick-action-icon">🧪</div>
                    <div class="quick-action-title">Data Lab</div>
                    <div class="quick-action-desc">Clean nulls, transform schema & aggregate.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Data Lab 🧪", key="home_qa_lab", use_container_width=True):
                st.session_state.target_nav = "🧪 Data Lab"
                st.rerun()

        with qa_col2:
            st.markdown(
                """
                <div class="quick-action-card">
                    <div class="quick-action-icon">📊</div>
                    <div class="quick-action-title">Visualizations</div>
                    <div class="quick-action-desc">Interactive line, bar, scatter & pie charts.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Visualizations 📊", key="home_qa_viz", use_container_width=True):
                st.session_state.target_nav = "📊 Visualization Studio"
                st.rerun()

            st.markdown(
                """
                <div class="quick-action-card" style="margin-top: 0.8rem;">
                    <div class="quick-action-icon">🔮</div>
                    <div class="quick-action-title">Prediction</div>
                    <div class="quick-action-desc">Regression, classification & forecasting.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Prediction 🔮", key="home_qa_pred", use_container_width=True):
                st.session_state.target_nav = "🔮 Prediction & Insights"
                st.rerun()

    # Suggested question chips below the main cards
    st.markdown("---")
    st.markdown("##### 💡 Suggested Questions")
    if st.session_state.df is not None and st.session_state.profile is not None:
        p_cards = get_default_prompt_cards(st.session_state.profile)
    else:
        p_cards = [
            {"icon": "💰", "title": "Total Revenue by Category", "prompt": "Show total revenue and profit by product category"},
            {"icon": "🏆", "title": "Top Performing Products", "prompt": "Which product category has the highest sales?"},
            {"icon": "🔮", "title": "Forecast Next 30 Days", "prompt": "Forecast revenue for the next 30 days"},
            {"icon": "🔍", "title": "Identify Outliers", "prompt": "Detect outliers and anomalies in the dataset"}
        ]
    chip_cols = st.columns(len(p_cards))
    for idx, pc in enumerate(p_cards):
        with chip_cols[idx]:
            if st.button(f"{pc['icon']} {pc['title']}", key=f"home_chip_{idx}", use_container_width=True, help=pc['prompt']):
                st.session_state.pending_query = pc['prompt']
                st.session_state.target_nav = "💬 Ask AI"
                st.rerun()

    # Recent Datasets section near the bottom
    st.markdown("---")
    st.markdown("##### 🕒 Recent Datasets")
    recent_samples = [
        {"name": "sales_data.csv", "rows": 1098, "cols": 12, "desc": "E-Commerce Revenue, Profit, Category", "file": "sales_data.csv"},
        {"name": "student_performance.xlsx", "rows": 1000, "cols": 11, "desc": "Academic Scores, Demographics", "file": "student_performance.xlsx", "sheet": "Exam_Scores"},
        {"name": "customer_churn.csv", "rows": 1000, "cols": 10, "desc": "Customer Churn, Tenure, Monthly Charges", "file": "customer_churn.csv"}
    ]
    r_cols = st.columns(3)
    for idx, s in enumerate(recent_samples):
        with r_cols[idx]:
            is_active_ds = (st.session_state.file_name == s["name"])
            st.markdown(
                f"""
                <div class="recent-dataset-item" style="{'border-color: ' + COLOR_PRIMARY + '; background: ' + COLOR_PALE_BLUE + ';' if is_active_ds else ''}">
                    <div style="font-weight: 600; color: {COLOR_TEXT_PRIMARY};">📄 {s['name']}</div>
                    <div style="font-size: 0.78rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 2px;">{s['rows']:,} rows × {s['cols']} cols • {s['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            btn_txt = "✓ Active Dataset" if is_active_ds else f"Load {s['name']}"
            if st.button(btn_txt, key=f"home_load_recent_{idx}", use_container_width=True, disabled=is_active_ds):
                p = os.path.join(SAMPLE_DATA_DIR, s["file"])
                if s.get("sheet"):
                    res = DataLoader.load(p, sheet_name=s["sheet"])
                    if res.success:
                        with open(p, "rb") as f:
                            b = f.read()
                        set_active_dataset(res.df, s["name"], sheets=res.sheets, active_sheet=s["sheet"], excel_bytes=b)
                        st.rerun()
                else:
                    res = DataLoader.load(p)
                    if res.success:
                        set_active_dataset(res.df, s["name"])
                        st.rerun()


# =============================================================
# 2. DATA WORKSPACE
# =============================================================
elif navigation == "📁 Data Workspace":
    render_page_header("Data Workspace", "Inspect schema, column distributions, and data quality metrics")

    if st.session_state.df is not None and st.session_state.profile is not None:
        df = st.session_state.df
        profile = st.session_state.profile

        # Dataset information bar & Change File action
        info_col, change_col = st.columns([4, 1])
        with info_col:
            render_dataset_info_bar(
                st.session_state.file_name,
                len(df),
                len(df.columns),
                active_sheet=st.session_state.active_sheet
            )
        with change_col:
            st.write("")
            show_change = st.expander("📁 Change File", expanded=False)

        with show_change:
            up_f = st.file_uploader("Upload new file", type=["csv", "xlsx", "xls"], key="ws_change_uploader")
            if up_f is not None:
                b_data = up_f.getvalue()
                ins_info = DataLoader.inspect_file(io.BytesIO(b_data), up_f.name)
                if ins_info.get("is_excel"):
                    s_name = st.selectbox("Select Sheet", ins_info["sheets"], key="ws_change_sheet")
                    if st.button("Load Sheet", type="primary", key="ws_change_btn_xl"):
                        l_res = DataLoader.load(io.BytesIO(b_data), up_f.name, sheet_name=s_name)
                        if l_res.success:
                            set_active_dataset(l_res.df, up_f.name, sheets=ins_info["sheets"], active_sheet=s_name, excel_bytes=b_data)
                            st.rerun()
                else:
                    if st.button("Load CSV", type="primary", key="ws_change_btn_csv"):
                        l_res = DataLoader.load(io.BytesIO(b_data), up_f.name)
                        if l_res.success:
                            set_active_dataset(l_res.df, up_f.name)
                            st.rerun()

        # Worksheet Switcher if multi-sheet Excel
        if st.session_state.excel_sheets and st.session_state.excel_bytes:
            sh_col1, sh_col2 = st.columns([3, 1])
            with sh_col1:
                cur_idx = st.session_state.excel_sheets.index(st.session_state.active_sheet) if st.session_state.active_sheet in st.session_state.excel_sheets else 0
                new_sheet = st.selectbox("Active Excel Worksheet:", st.session_state.excel_sheets, index=cur_idx, key="ws_switch_select")
            with sh_col2:
                st.write("")
                st.write("")
                if st.button("Switch Sheet", type="secondary", key="ws_switch_btn"):
                    load_res = DataLoader.load(io.BytesIO(st.session_state.excel_bytes), st.session_state.file_name, sheet_name=new_sheet)
                    if load_res.success:
                        set_active_dataset(load_res.df, st.session_state.file_name, sheets=st.session_state.excel_sheets, active_sheet=new_sheet, excel_bytes=st.session_state.excel_bytes)
                        st.rerun()

        # Below the dataset bar: Overview, Data Preview, Schema, Quality Report tabs
        t_overview, t_preview, t_schema, t_quality = st.tabs([
            "Overview", "Data Preview", "Schema", "Quality Report"
        ])

        with t_overview:
            # Compact cards for Rows, Columns, Missing Values, and Duplicates
            k_c1, k_c2, k_c3, k_c4 = st.columns(4)
            with k_c1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Rows</div>
                        <div class="kpi-value">{profile.row_count:,}</div>
                        <div class="kpi-sub">Total Records</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k_c2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Columns</div>
                        <div class="kpi-value">{profile.column_count}</div>
                        <div class="kpi-sub">{len(profile.numerical_columns)} Num • {len(profile.categorical_columns)} Cat</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k_c3:
                sub_c = COLOR_SUCCESS if profile.missing_pct == 0 else COLOR_WARNING
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Missing Values</div>
                        <div class="kpi-value">{profile.missing_cells:,}</div>
                        <div class="kpi-sub" style="color: {sub_c};">{profile.missing_pct}% of total cells</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k_c4:
                dup_c = COLOR_SUCCESS if profile.duplicate_rows == 0 else COLOR_ERROR
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">Duplicates</div>
                        <div class="kpi-value">{profile.duplicate_rows:,}</div>
                        <div class="kpi-sub" style="color: {dup_c};">{profile.duplicate_pct}% duplicate rate</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.write("")
            # Dataset Summary card & Dataset Quality panel
            sum_col, qual_col = st.columns([3, 2], gap="medium")
            with sum_col:
                st.markdown(
                    f"""
                    <div class="white-content-card">
                        <div class="content-card-title">📝 Dataset Summary</div>
                        <div style="font-size: 0.88rem; line-height: 1.5; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 0.75rem;">
                            {profile.plain_english_summary}
                        </div>
                        <div style="font-size: 0.8rem; color: {COLOR_TEXT_SECONDARY};">
                            <b>Memory Footprint:</b> {profile.memory_usage_mb} MB • 
                            <b>Primary Candidate:</b> <code>{profile.potential_targets[0] if profile.potential_targets else 'None'}</code>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with qual_col:
                cleanliness_score = max(0, int(100 - (profile.missing_pct * 1.5 + profile.duplicate_pct * 2.0)))
                gauge_color = COLOR_SUCCESS if cleanliness_score >= 85 else (COLOR_WARNING if cleanliness_score >= 70 else COLOR_ERROR)
                rating_label = "Excellent" if cleanliness_score >= 85 else ("Good" if cleanliness_score >= 70 else "Needs Cleaning")
                st.markdown(
                    f"""
                    <div class="white-content-card" style="text-align: center;">
                        <div class="content-card-title" style="text-align: left;">🛡️ Dataset Quality</div>
                        <div style="margin: 0.6rem 0;">
                            <div style="font-size: 2.2rem; font-weight: 700; color: {gauge_color};">{cleanliness_score}%</div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: {gauge_color};">Health Rating: {rating_label}</div>
                        </div>
                        <div style="font-size: 0.78rem; color: {COLOR_TEXT_SECONDARY};">
                            Completeness: {100 - profile.missing_pct:.1f}% • Uniqueness: {100 - profile.duplicate_pct:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Column Information table
            st.markdown("##### 📋 Column Information")
            col_info_list = []
            for c_name, c_prof in profile.columns.items():
                col_info_list.append({
                    "Column Name": c_name,
                    "Inferred Type": c_prof.inferred_type.capitalize(),
                    "Missing Count": c_prof.null_count,
                    "Missing Pct": f"{c_prof.null_pct}%",
                    "Unique Values": c_prof.unique_count,
                    "Sample Values": ", ".join([str(v) for v in c_prof.sample_values[:3]])
                })
            st.dataframe(pd.DataFrame(col_info_list), use_container_width=True)

        with t_preview:
            st.markdown("##### 🔍 Data Preview")
            prev_slider = st.slider("Display records:", min_value=5, max_value=min(100, len(df)), value=min(25, len(df)), key="ws_prev_slider_num")
            search_term = st.text_input("Filter preview rows (search):", placeholder="Type keywords...", key="ws_prev_search")
            if search_term.strip():
                mask = df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
                st.dataframe(df[mask].head(prev_slider), use_container_width=True)
            else:
                st.dataframe(df.head(prev_slider), use_container_width=True)

        with t_schema:
            st.markdown("##### 📋 Detailed Schema & Data Types")
            schema_full = []
            for c_name, c_prof in profile.columns.items():
                schema_full.append({
                    "Column Name": c_name,
                    "Storage Dtype": c_prof.dtype,
                    "Inferred Type": c_prof.inferred_type.capitalize(),
                    "Null Count": c_prof.null_count,
                    "Null Pct": f"{c_prof.null_pct}%",
                    "Distinct Values": c_prof.unique_count,
                    "Sample 1": str(c_prof.sample_values[0]) if len(c_prof.sample_values) > 0 else "",
                    "Sample 2": str(c_prof.sample_values[1]) if len(c_prof.sample_values) > 1 else "",
                    "Sample 3": str(c_prof.sample_values[2]) if len(c_prof.sample_values) > 2 else ""
                })
            st.dataframe(pd.DataFrame(schema_full), use_container_width=True)

        with t_quality:
            st.markdown("##### 🧹 Dataset Quality & Hygiene Report")
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                st.markdown("###### Null / Missing Distribution")
                null_dict = {col: p.null_count for col, p in profile.columns.items() if p.null_count > 0}
                if null_dict:
                    null_df = pd.DataFrame(list(null_dict.items()), columns=["Column", "Missing Cells"]).sort_values("Missing Cells", ascending=False)
                    st.dataframe(null_df, use_container_width=True)
                else:
                    st.success("✅ Clean dataset: Zero missing cells detected across all columns.")
            with q_col2:
                st.markdown("###### Duplicate Row Analysis")
                if profile.duplicate_rows > 0:
                    st.warning(f"⚠️ Detected {profile.duplicate_rows:,} duplicate rows ({profile.duplicate_pct}% of total dataset).")
                else:
                    st.success("✅ No duplicate records detected.")
    else:
        st.info("No active dataset loaded. Please upload a file above or pick a sample dataset.")


# =============================================================
# 3. ASK AI (CHATGPT-STYLE CHATBOT)
# =============================================================
elif navigation == "💬 Ask AI":
    h_col1, h_col2 = st.columns([4.2, 1])
    with h_col1:
        render_page_header(
            "Ask AI",
            "Ask questions in plain English and get instant data analysis, charts, and business insights."
        )
    with h_col2:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("➕ New Chat", key="chat_new_btn", use_container_width=True):
            create_new_conversation("Data Discovery")
            st.rerun()

    if st.session_state.df is not None:
        render_dataset_info_bar(
            file_name=st.session_state.file_name,
            row_count=len(st.session_state.df),
            col_count=len(st.session_state.df.columns),
            active_sheet=st.session_state.active_sheet
        )

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home to begin analysis.")
    else:
        active_messages = get_active_messages()
        clicked_chip = None
        if st.session_state.get("pending_query"):
            clicked_chip = st.session_state.pop("pending_query")

        # Welcome screen if no messages in active conversation
        clicked_prompt = None
        if not active_messages:
            render_chat_welcome()
            cards = get_default_prompt_cards(st.session_state.profile)
            p_cols = st.columns(2)
            for idx, c in enumerate(cards):
                with p_cols[idx % 2]:
                    st.markdown(
                        f"""
                        <div class="prompt-card">
                            <div class="prompt-card-icon">{c['icon']}</div>
                            <div class="prompt-card-text">{c['title']}</div>
                            <div class="prompt-card-desc">{c['desc']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(f"Ask: {c['prompt']}", key=f"pcard_{idx}", use_container_width=True):
                        clicked_prompt = c["prompt"]

        # Render Conversation Message Bubbles
        retry_query = None
        for i, msg in enumerate(active_messages):
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="📊"):
                    st.markdown('<div class="assistant-badge">● InsightFlow Analyst</div>', unsafe_allow_html=True)
                    st.markdown(msg["content"])

                    if msg.get("formula"):
                        st.markdown(f'<div class="formula-pill">Formula: {msg["formula"]}</div>', unsafe_allow_html=True)
                        with st.expander("🔬 Formula & Execution Details", expanded=False):
                            st.markdown(f"**Verified Execution Formula**: `{msg['formula']}`")
                            st.caption("Computed deterministically via Pandas/NumPy execution pipeline. Zero LLM math hallucination.")

                    if msg.get("figure") is not None:
                        st.plotly_chart(msg["figure"], use_container_width=True)
                        if st.session_state.profile and st.session_state.profile.numerical_columns:
                            c_anom = st.session_state.profile.numerical_columns[0]
                            if st.button(f"🔍 Analyze Anomalies in {c_anom}", key=f"anom_btn_{i}"):
                                clicked_chip = f"Detect outliers and anomalies in {c_anom}"

                    if msg.get("table") is not None:
                        with st.expander("📊 View Data Table", expanded=True):
                            tbl_df = msg["table"]
                            if len(tbl_df) > 5:
                                top_n = st.slider("Display records:", min_value=5, max_value=min(100, len(tbl_df)), value=min(10, len(tbl_df)), key=f"slicer_{i}")
                                st.dataframe(tbl_df.head(top_n), use_container_width=True)
                            else:
                                st.dataframe(tbl_df, use_container_width=True)
                            csv_b = DataExporter.to_csv_bytes(tbl_df)
                            st.download_button(
                                "📥 Download Table (CSV)",
                                data=csv_b,
                                file_name="analysis_table.csv",
                                mime="text/csv",
                                key=f"dl_tbl_{i}"
                            )

                    # Copy response / actions bar
                    act_c1, act_c2 = st.columns([4, 1])
                    with act_c1:
                        with st.expander("📋 Copy Response Text", expanded=False):
                            st.code(msg["content"], language="markdown")
                    with act_c2:
                        if msg.get("has_error"):
                            if st.button("🔄 Retry", key=f"retry_{i}"):
                                # Find prior user query
                                for prev_m in reversed(active_messages[:i]):
                                    if prev_m["role"] == "user":
                                        retry_query = prev_m["content"]
                                        break

        # Dynamic Follow-up Action Chips below chat
        if active_messages and active_messages[-1]["role"] == "assistant":
            last_u_query = ""
            for m in reversed(active_messages):
                if m["role"] == "user":
                    last_u_query = m["content"]
                    break
            fup_chips = get_follow_up_action_chips(last_u_query, st.session_state.profile)
            if fup_chips:
                st.markdown("###### ⚡ Suggested Follow-up Questions")
                f_cols = st.columns(len(fup_chips))
                for f_i, fc in enumerate(fup_chips):
                    with f_cols[f_i]:
                        if st.button(fc["label"], key=f"fup_btn_{f_i}_{len(active_messages)}", use_container_width=True):
                            clicked_chip = fc["query"]

        # Message Input Composer
        user_input = st.chat_input("Ask a question about your data (Shift+Enter for newline)...")
        active_query = retry_query or clicked_chip or clicked_prompt or user_input

        if active_query:
            # 1. Append User Message
            active_messages.append({"role": "user", "content": active_query})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(active_query)

            # 2. Assistant Streaming Response
            with st.chat_message("assistant", avatar="📊"):
                st.markdown('<div class="assistant-badge">● InsightFlow Analyst</div>', unsafe_allow_html=True)
                
                # Execute tool deterministically & stream explanation
                with st.spinner("Analyzing schema, executing deterministic calculation, and verifying output..."):
                    stream_iter, meta = AnalystAgent.run_stream(
                        query=active_query,
                        df=st.session_state.df,
                        profile=st.session_state.profile,
                        chat_history=active_messages,
                        api_key=st.session_state.groq_api_key,
                        model_name=st.session_state.selected_model
                    )

                # Real token streaming rendering
                full_response = st.write_stream(stream_iter)

                # Render formula pill if present
                if meta.get("formula"):
                    st.markdown(f'<div class="formula-pill">Formula: {meta["formula"]}</div>', unsafe_allow_html=True)
                    with st.expander("🔬 Formula & Execution Details", expanded=False):
                        st.markdown(f"**Verified Execution Formula**: `{meta['formula']}`")
                        st.caption("Computed deterministically via Pandas/NumPy execution pipeline. Zero LLM math hallucination.")

                # Render attached Plotly figure if generated
                if meta.get("figure") is not None:
                    st.plotly_chart(meta["figure"], use_container_width=True)

                # Render attached Table if generated
                if meta.get("table") is not None:
                    with st.expander("📊 View Data Table", expanded=True):
                        tbl_out = meta["table"]
                        if len(tbl_out) > 5:
                            slicer_out = st.slider("Display records:", min_value=5, max_value=min(100, len(tbl_out)), value=min(10, len(tbl_out)), key=f"slicer_stream_{len(active_messages)}")
                            st.dataframe(tbl_out.head(slicer_out), use_container_width=True)
                        else:
                            st.dataframe(tbl_out, use_container_width=True)
                        csv_b = DataExporter.to_csv_bytes(tbl_out)
                        st.download_button(
                            "📥 Download Table (CSV)",
                            data=csv_b,
                            file_name="analysis_table.csv",
                            mime="text/csv",
                            key=f"dl_tbl_{len(active_messages)}"
                        )

            # 3. Save Assistant Message in Conversation History
            active_messages.append({
                "role": "assistant",
                "content": full_response,
                "formula": meta.get("formula"),
                "figure": meta.get("figure"),
                "table": meta.get("table"),
                "has_error": not meta.get("success", True)
            })

            # Auto-title conversation from first query
            if len(active_messages) <= 2:
                st.session_state.conversations[st.session_state.active_conv_id]["title"] = active_query[:25]


# =============================================================
# 4. VISUALIZATION STUDIO
# =============================================================
elif navigation == "📊 Visualization Studio":
    render_page_header("Visualization Studio", "Interactive visual analytics and custom charts")

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home.")
    else:
        df = st.session_state.df
        profile = st.session_state.profile

        tab_quick, tab_custom = st.tabs(["Quick Charts", "Custom Chart"])

        with tab_quick:
            st.markdown("##### ⚡ Quick Recommended Visualizations")
            qc_row1 = st.columns(2)
            num_cols = profile.numerical_columns
            cat_cols = profile.categorical_columns
            dt_cols = profile.datetime_columns or [c for c in df.columns if "date" in c.lower()]

            with qc_row1[0]:
                if cat_cols and num_cols:
                    b_fig = DataVisualizer.build_chart(df, chart_type="bar", x_col=cat_cols[0], y_col=num_cols[0], title=f"{num_cols[0]} by {cat_cols[0]}", top_n=8)
                    if b_fig.fig:
                        st.plotly_chart(b_fig.fig, use_container_width=True)
                else:
                    st.info("Category breakdown requires at least one categorical and numerical column.")

            with qc_row1[1]:
                if num_cols:
                    h_fig = DataVisualizer.build_chart(df, chart_type="histogram", x_col=num_cols[0], title=f"Distribution of {num_cols[0]}")
                    if h_fig.fig:
                        st.plotly_chart(h_fig.fig, use_container_width=True)
                else:
                    st.info("Histogram requires numerical columns.")

            qc_row2 = st.columns(2)
            with qc_row2[0]:
                if dt_cols and num_cols:
                    l_fig = DataVisualizer.build_chart(df, chart_type="line", x_col=dt_cols[0], y_col=num_cols[0], title=f"{num_cols[0]} over Time")
                    if l_fig.fig:
                        st.plotly_chart(l_fig.fig, use_container_width=True)
                elif len(num_cols) >= 2:
                    s_fig = DataVisualizer.build_chart(df, chart_type="scatter", x_col=num_cols[0], y_col=num_cols[1], title=f"{num_cols[1]} vs {num_cols[0]}")
                    if s_fig.fig:
                        st.plotly_chart(s_fig.fig, use_container_width=True)
                else:
                    st.caption("Add date or second numerical column for trend or scatter plot.")

            with qc_row2[1]:
                if len(num_cols) >= 2:
                    hm_fig = DataVisualizer.build_chart(df, chart_type="heatmap", title="Correlation Matrix")
                    if hm_fig.fig:
                        st.plotly_chart(hm_fig.fig, use_container_width=True)
                else:
                    st.caption("Requires at least 2 numerical columns for correlation matrix.")

        with tab_custom:
            c_ctrl, c_view = st.columns([1, 3], gap="medium")

            with c_ctrl:
                st.markdown(
                    """
                    <div class="white-content-card">
                        <div class="content-card-title">⚙️ Chart Controls</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                chart_type = st.selectbox(
                    "Chart Type",
                    ["Bar", "Line", "Area", "Pie", "Donut", "Histogram", "Scatter", "Box", "Correlation Heatmap"],
                    key="vs_chart_type"
                )
                all_cols = list(df.columns)
                num_cols = profile.numerical_columns
                cat_cols = profile.categorical_columns

                x_val = st.selectbox("X Axis", [None] + all_cols, index=1 if all_cols else 0, key="vs_x")
                y_val = st.selectbox("Y Axis", [None] + num_cols + all_cols, index=1 if num_cols else 0, key="vs_y")
                color_val = st.selectbox("Group By (Color)", [None] + cat_cols + all_cols, index=0, key="vs_color")
                agg_mode = st.selectbox("Aggregation", ["Sum", "Mean", "Count", "Min", "Max"], index=0, key="vs_agg")
                c_title = st.text_input("Chart Title", value=f"{chart_type} of {y_val or ''} by {x_val or ''}".strip(), key="vs_title")

                if st.button("💡 Auto-Recommend", type="secondary", key="vs_auto_rec", use_container_width=True):
                    rec = DataVisualizer.recommend_best_chart(df)
                    st.info(f"Recommended: **{rec['chart_type'].title()}** ({rec['reason']})")

            with c_view:
                c_name = chart_type.lower().replace(" ", "_")
                if c_name == "correlation_heatmap":
                    c_name = "heatmap"

                res = DataVisualizer.build_chart(
                    df=df,
                    chart_type=c_name,
                    x_col=x_val,
                    y_col=y_val,
                    color_col=color_val,
                    title=c_title
                )

                if res.success and res.fig is not None:
                    st.plotly_chart(res.fig, use_container_width=True)

                    # Insight/explanation panel below chart
                    st.markdown(
                        f"""
                        <div class="white-content-card" style="border-left: 4px solid {COLOR_PRIMARY};">
                            <div class="content-card-title">💡 Visual Analytical Insight</div>
                            <div style="font-size: 0.85rem; color: {COLOR_TEXT_SECONDARY}; line-height: 1.5;">
                                {res.rationale}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Download Chart and Save to Report actions
                    a_c1, a_c2 = st.columns(2)
                    with a_c1:
                        html_bytes = res.fig.to_html(include_plotlyjs="cdn").encode("utf-8")
                        st.download_button(
                            "📥 Download Chart (HTML)",
                            data=html_bytes,
                            file_name=f"{c_name}_chart.html",
                            mime="text/html",
                            use_container_width=True
                        )
                    with a_c2:
                        if st.button("📑 Save to Report", key="vs_save_to_report", use_container_width=True):
                            st.success("Chart saved to session report queue!")
                else:
                    st.error(res.error)


# =============================================================
# 5. DATA LAB (CLEANING, TRANSFORMATIONS, MERGE & CONVERSION)
# =============================================================
elif navigation == "🧪 Data Lab":
    render_page_header("Data Lab", "Data transformation, cleaning, and preparation suite")

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home.")
    else:
        df = st.session_state.df
        history: CleaningHistory = st.session_state.cleaning_history

        # 4 Tabs matching reference: Cleaning, Transformations, Merge & Reshape, Conversion
        t_clean, t_trans, t_merge, t_conv = st.tabs([
            "Cleaning", "Transformations", "Merge & Reshape", "Conversion"
        ])

        with t_clean:
            st.markdown("##### 🧹 Data Cleaning Operations")
            c_op = st.selectbox("Cleaning Operation:", ["Remove Duplicates", "Handle Missing Values", "Trim Outliers (IQR Inspector)"], key="dl_clean_op")

            if c_op == "Remove Duplicates":
                sub = st.multiselect("Columns subset (leave empty for entire row):", list(df.columns), key="dl_dup_sub")
                dup_count = df.duplicated(subset=sub if sub else None).sum()
                st.write(f"Detected **{dup_count:,} duplicate rows** in active dataset.")

                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("Preview Cleaned Dataset", type="secondary", disabled=(dup_count == 0), key="dl_prev_dup"):
                        prev_clean, _ = DataCleaner.remove_duplicates(df, subset=sub if sub else None)
                        st.dataframe(prev_clean.head(10), use_container_width=True)
                with c_b2:
                    if st.button("Execute Deduplication", type="primary", disabled=(dup_count == 0), key="dl_exec_dup"):
                        cleaned_df, removed = DataCleaner.remove_duplicates(df, subset=sub if sub else None)
                        history.record_action("deduplication", f"Removed {removed:,} duplicates", {"subset": sub}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(f"Successfully removed {removed:,} duplicate rows!")
                        st.rerun()

            elif c_op == "Handle Missing Values":
                strat = st.selectbox("Strategy:", ["mean", "median", "mode", "drop_rows", "drop_cols", "ffill", "bfill", "constant"], key="dl_null_strat")
                cols_to_handle = st.multiselect("Target columns (leave empty for all):", list(df.columns), key="dl_null_cols")
                const_val = st.text_input("Constant value:") if strat == "constant" else None

                if st.button("Apply Missing Value Treatment", type="primary", key="dl_exec_null"):
                    try:
                        cleaned_df, stats = DataCleaner.handle_missing_values(df, strategy=strat, columns=cols_to_handle if cols_to_handle else None, fill_value=const_val)
                        history.record_action("missing_values", f"Handled nulls using {strat}", {"strategy": strat, "stats": stats}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(f"Missing values handled using strategy '{strat}'.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error handling missing values: {e}")

            elif c_op == "Trim Outliers (IQR Inspector)":
                num_cols = profile.numerical_columns
                if not num_cols:
                    st.warning("No numerical columns found.")
                else:
                    c_out = st.selectbox("Select Numerical Feature:", num_cols, key="dl_out_col")
                    iqr_mult = st.slider("IQR Multiplier:", min_value=1.0, max_value=3.5, value=1.5, step=0.1, key="dl_out_iqr")
                    outlier_fig = DataVisualizer.build_outlier_inspector(df, c_out, iqr_mult)
                    st.plotly_chart(outlier_fig, use_container_width=True)

                    s_col = pd.to_numeric(df[c_out], errors="coerce")
                    q1 = float(s_col.quantile(0.25))
                    q3 = float(s_col.quantile(0.75))
                    iqr_val = q3 - q1
                    low_b = q1 - iqr_mult * iqr_val
                    high_b = q3 + iqr_mult * iqr_val
                    outliers_detected = int(((s_col < low_b) | (s_col > high_b)).sum())

                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Anomalies Detected", f"{outliers_detected:,} rows", delta=f"{round(outliers_detected/len(df)*100, 1)}% of dataset", delta_color="inverse")
                    col_m2.metric("Valid Range Window", f"[{low_b:,.2f} to {high_b:,.2f}]")

                    if st.button("✂️ Trim Outliers", type="primary", disabled=(outliers_detected == 0), key="dl_exec_trim"):
                        trimmed_df, removed, l_b, u_b = DataCleaner.trim_outliers(df, c_out, iqr_mult)
                        history.record_action("trim_outliers", f"Trimmed {removed:,} outliers in '{c_out}'", {"column": c_out, "multiplier": iqr_mult, "removed": removed}, df, trimmed_df)
                        st.session_state.df = trimmed_df
                        st.session_state.profile = DataProfiler.profile(trimmed_df)
                        st.success(f"Successfully trimmed {removed:,} outlier rows!")
                        st.rerun()

        with t_trans:
            st.markdown("##### ⚡ Data Transformation Operations")
            t_op = st.selectbox("Transformation Operation:", ["Change Data Types", "Rename Columns", "Filter Records", "Sort Records", "Create Derived Column (AST Evaluator)"], key="dl_trans_op")

            if t_op == "Change Data Types":
                col_target = st.selectbox("Select column to cast:", list(df.columns), key="dl_cast_col")
                t_type = st.selectbox("Target Data Type:", ["numeric", "integer", "string", "categorical", "datetime", "boolean"], key="dl_cast_type")
                dt_fmt = st.text_input("Date format (Optional, e.g. %Y-%m-%d):", value="", key="dl_cast_fmt") if t_type == "datetime" else None
                if st.button("Convert Type", type="primary", key="dl_exec_cast"):
                    try:
                        cleaned_df, msg = DataCleaner.convert_column_type(df, col_target, t_type, date_format=dt_fmt or None)
                        history.record_action("type_cast", msg, {"column": col_target, "type": t_type}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Type conversion failed: {e}")

            elif t_op == "Rename Columns":
                old_name = st.selectbox("Column to rename:", list(df.columns), key="dl_ren_old")
                new_name = st.text_input("New column name:", value=f"{old_name}_Clean", key="dl_ren_new")
                if st.button("Rename Column", type="primary", key="dl_exec_rename"):
                    cleaned_df = DataCleaner.rename_columns(df, {old_name: new_name})
                    history.record_action("rename", f"Renamed '{old_name}' to '{new_name}'", {"old": old_name, "new": new_name}, df, cleaned_df)
                    st.session_state.df = cleaned_df
                    st.session_state.profile = DataProfiler.profile(cleaned_df)
                    st.success(f"Renamed '{old_name}' to '{new_name}'.")
                    st.rerun()

            elif t_op == "Filter Records":
                f_col = st.selectbox("Filter Column:", list(df.columns), key="dl_flt_col")
                f_op = st.selectbox("Operator:", ["==", "!=", ">", ">=", "<", "<=", "contains", "not_null", "is_null"], key="dl_flt_op")
                f_val = st.text_input("Value:", key="dl_flt_val")
                if st.button("Apply Filter", type="primary", key="dl_exec_filter"):
                    try:
                        cleaned_df = DataCleaner.filter_records(df, f_col, f_op, f_val)
                        history.record_action("filter", f"Filtered {f_col} {f_op} {f_val}", {"column": f_col, "op": f_op, "val": f_val}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(f"Filtered dataset to {len(cleaned_df):,} rows.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Filter error: {e}")

            elif t_op == "Sort Records":
                s_col = st.selectbox("Sort by Column:", list(df.columns), key="dl_sort_col")
                s_order = st.radio("Sort Order:", ["Ascending", "Descending"], horizontal=True, key="dl_sort_ord")
                if st.button("Sort Dataset", type="primary", key="dl_exec_sort"):
                    cleaned_df = DataCleaner.sort_records(df, by=[s_col], ascending=(s_order == "Ascending"))
                    history.record_action("sort", f"Sorted by {s_col} ({s_order})", {"by": s_col, "ascending": (s_order == "Ascending")}, df, cleaned_df)
                    st.session_state.df = cleaned_df
                    st.session_state.profile = DataProfiler.profile(cleaned_df)
                    st.success(f"Sorted dataset by {s_col} ({s_order}).")
                    st.rerun()

            elif t_op == "Create Derived Column (AST Evaluator)":
                st.caption("Supports math expressions like `Revenue - Cost` or `(Profit / Revenue) * 100` via AST.")
                new_c_name = st.text_input("New Column Name:", value="Gross_Profit", key="dl_der_name")
                expr = st.text_input("Formula Expression:", value="Revenue - Cost", key="dl_der_expr")
                if expr.strip():
                    try:
                        preview_series = SafeFormulaEvaluator.evaluate(expr, df.head(5))
                        st.success(f"✅ **Valid Expression** • Preview (first 5): `{list(preview_series.round(2))}`")
                    except Exception as p_err:
                        st.info(f"💡 Expression check: {p_err}")
                if st.button("Add Derived Column", type="primary", key="dl_exec_der"):
                    try:
                        cleaned_df, msg = DataCleaner.create_derived_column(df, new_c_name, expr)
                        history.record_action("derived_column", msg, {"name": new_c_name, "expr": expr}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Formula evaluation error: {e}")

        with t_merge:
            st.markdown("##### 🔀 Merge & Reshape Operations")
            m_op = st.selectbox("Reshape Operation:", ["Group & Aggregate", "Pivot Dataset"], key="dl_merge_op")
            if m_op == "Group & Aggregate":
                g_col = st.selectbox("Group by Category Column:", list(df.columns), key="dl_grp_col")
                num_cols = profile.numerical_columns or list(df.columns)
                v_col = st.selectbox("Target Metric Column:", num_cols, key="dl_grp_metric")
                agg_func = st.selectbox("Aggregation Function:", ["sum", "mean", "count", "min", "max"], key="dl_grp_agg")
                if st.button("Execute Aggregation", type="primary", key="dl_exec_grp"):
                    try:
                        cleaned_df = DataCleaner.group_and_aggregate(df, g_col, v_col, agg_func=agg_func)
                        history.record_action("group_agg", f"Aggregated {v_col} ({agg_func}) by {g_col}", {"group_col": g_col, "metric": v_col, "agg": agg_func}, df, cleaned_df)
                        st.session_state.df = cleaned_df
                        st.session_state.profile = DataProfiler.profile(cleaned_df)
                        st.success(f"Aggregated {v_col} by {g_col}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Aggregation error: {e}")
            else:
                p_idx = st.selectbox("Index / Row Dimension:", list(df.columns), index=0, key="dl_piv_idx")
                p_cols = st.selectbox("Columns Dimension:", list(df.columns), index=1 if len(df.columns) > 1 else 0, key="dl_piv_cols")
                p_val = st.selectbox("Values Column:", profile.numerical_columns or list(df.columns), key="dl_piv_val")
                p_agg = st.selectbox("Aggregation:", ["mean", "sum", "count", "min", "max"], key="dl_piv_agg")
                if st.button("Execute Pivot Table", type="primary", key="dl_exec_piv"):
                    try:
                        pivoted_df = DataCleaner.pivot_data(df, p_idx, p_cols, p_val, aggfunc=p_agg)
                        history.record_action("pivot", f"Pivoted {p_val} by {p_idx} × {p_cols}", {"index": p_idx, "cols": p_cols, "val": p_val}, df, pivoted_df)
                        st.session_state.df = pivoted_df
                        st.session_state.profile = DataProfiler.profile(pivoted_df)
                        st.success("Pivot table generated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Pivot error: {e}")

        with t_conv:
            st.markdown("##### 🔄 Format Conversion & Date Parsing")
            st.caption("Convert date format across timestamp features or transform dataset encodings.")
            dt_cols = profile.datetime_columns or [c for c in df.columns if "date" in c.lower()]
            if dt_cols:
                d_c = st.selectbox("Select Date Column:", dt_cols, key="dl_conv_date_col")
                d_fmt = st.selectbox("Target Date Format:", ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"], key="dl_conv_fmt")
                if st.button("Reformat Date Column", type="primary", key="dl_exec_date_conv"):
                    try:
                        df[d_c] = pd.to_datetime(df[d_c], errors="coerce").dt.strftime(d_fmt)
                        st.session_state.df = df
                        st.session_state.profile = DataProfiler.profile(df)
                        st.success(f"Reformatted '{d_c}' to {d_fmt}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Date formatting error: {e}")
            else:
                st.info("No datetime columns detected. Use 'Change Data Types' in Transformations tab to parse date strings.")

        # Transformation Audit Trail & Undo/Reset Controls
        st.markdown("---")
        st.markdown("#### 📜 Transformation Audit Trail")
        if history.actions:
            audit_records = []
            for a in history.actions:
                audit_records.append({
                    "Timestamp": a.timestamp,
                    "Action": a.action_type,
                    "Description": a.description,
                    "Rows Before": a.rows_before,
                    "Rows After": a.rows_after,
                    "Cols Before": a.cols_before,
                    "Cols After": a.cols_after
                })
            st.dataframe(pd.DataFrame(audit_records), use_container_width=True)

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                if st.button("↩️ Undo Last Transformation", type="secondary", key="dl_btn_undo"):
                    undone_df = history.undo_last()
                    if undone_df is not None:
                        st.session_state.df = undone_df
                        st.session_state.profile = DataProfiler.profile(undone_df)
                        st.success("Successfully reverted the last transformation step!")
                        st.rerun()
                    else:
                        st.info("No prior transformation to undo.")
            with r_col2:
                if st.button("🔄 Reset to Original Dataset", type="secondary", key="dl_btn_reset"):
                    reset_df = history.reset_to_original()
                    st.session_state.df = reset_df
                    st.session_state.profile = DataProfiler.profile(reset_df)
                    st.success("Dataset successfully reset to original state!")
                    st.rerun()
        else:
            st.caption("No transformations applied yet. Dataset is currently in original uploaded state.")


# =============================================================
# 6. PREDICTION & INSIGHTS (ML & TIME SERIES)
# =============================================================
elif navigation == "🔮 Prediction & Insights":
    render_page_header(
        "Prediction & Insights",
        "Train machine learning models, forecast future trends, and simulate 'what-if' business scenarios."
    )

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home to begin predictive modeling.")
    else:
        df = st.session_state.df
        profile = st.session_state.profile

        tab_fc, tab_cls, tab_reg = st.tabs(["📈 Forecasting", "🏷️ Classification", "🎯 Regression"])

        # Tab 1: Time Series Forecasting
        with tab_fc:
            fc_col_cfg, fc_col_res = st.columns([1, 2.2])

            with fc_col_cfg:
                st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
                st.markdown("###### ⚙️ Forecast Configuration")
                dt_cols = profile.datetime_columns or [c for c in df.columns if "date" in c.lower()]
                num_cols = profile.numerical_columns

                ts_date = st.selectbox("Date / Timestamp Column", dt_cols or list(df.columns), key="fc_date_col")
                ts_val = st.selectbox("Target Volume Column", num_cols or list(df.columns), key="fc_val_col")
                horizon = st.slider("Forecast Horizon (Periods)", min_value=7, max_value=90, value=30, step=7, key="fc_horizon")
                conf_level = st.selectbox("Confidence Level:", [0.95, 0.90, 0.80], index=0, format_func=lambda x: f"{int(x*100)}% Confidence", key="fc_conf")

                run_fc_btn = st.button("Run Time-Series Forecast", type="primary", use_container_width=True, key="run_fc_btn")
                st.markdown('</div>', unsafe_allow_html=True)

            with fc_col_res:
                if run_fc_btn:
                    with st.spinner("Executing time-series regression and confidence interval projection..."):
                        p_res = DataPredictor.forecast_timeseries(df, ts_date, ts_val, horizon_periods=horizon, confidence_level=conf_level)
                        st.session_state.ts_forecast_res = p_res

                if st.session_state.get("ts_forecast_res"):
                    p_res = st.session_state.ts_forecast_res
                    if p_res.success:
                        st.success("✅ Time-series projection generated successfully!")

                        # Model Performance / Parameters Cards
                        m_c1, m_c2, m_c3 = st.columns(3)
                        m_c1.metric("Forecast Horizon", f"{horizon} Periods")
                        m_c2.metric("Confidence Level", f"{int(conf_level*100)}%")
                        m_c3.metric("Projected Trend", "Autoregressive Drift")

                        # Large Chart Area
                        if p_res.forecast_chart:
                            st.plotly_chart(p_res.forecast_chart, use_container_width=True)

                        # Key Insights Panel
                        st.markdown(
                            f"""
                            <div class="key-insights-card">
                                <div class="key-insights-title">💡 Forecasting Key Insights</div>
                                <div>{p_res.executive_summary}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Projection Table & Download
                        if p_res.forecast_table is not None:
                            with st.expander("📊 View Forecast Table & Projection"):
                                st.dataframe(p_res.forecast_table, use_container_width=True)
                                csv_fc = DataExporter.to_csv_bytes(p_res.forecast_table)
                                st.download_button("📥 Download Forecast (CSV)", data=csv_fc, file_name="forecast_results.csv", mime="text/csv", key="dl_fc_csv")

                        with st.expander("⚠️ Assumptions & Model Limitations"):
                            for lim in p_res.limitations:
                                st.caption(f"• {lim}")
                    else:
                        st.error(p_res.error)
                else:
                    st.markdown(
                        """
                        <div class="empty-state-card">
                            <div class="empty-state-icon">📈</div>
                            <div class="empty-state-title">Ready for Time-Series Forecasting</div>
                            <div class="empty-state-desc">Select your date column and target metric on the left, then click <b>Run Time-Series Forecast</b> to project future values with confidence bands.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Tab 2: Classification
        with tab_cls:
            cls_col_cfg, cls_col_res = st.columns([1, 2.2])

            with cls_col_cfg:
                st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
                st.markdown("###### ⚙️ Classifier Configuration")
                cat_targets = profile.potential_targets or profile.categorical_columns or list(df.columns)
                t_col_cls = st.selectbox("Target Column (Categorical):", cat_targets, key="cls_target")
                m_type_cls = st.selectbox("Classifier Architecture:", ["random_forest", "gradient_boosting", "logistic"], key="cls_arch")

                run_cls_btn = st.button("Train Classification Model", type="primary", use_container_width=True, key="run_cls_btn")
                st.markdown('</div>', unsafe_allow_html=True)

            with cls_col_res:
                if run_cls_btn:
                    with st.spinner("Training classifier on stratified holdout test split..."):
                        p_res = DataPredictor.train_classification(df, target_col=t_col_cls, model_type=m_type_cls)
                        st.session_state.classification_model_res = p_res

                if st.session_state.get("classification_model_res"):
                    p_res = st.session_state.classification_model_res
                    if p_res.success:
                        st.success("✅ Model trained and evaluated on 20% stratified holdout set!")

                        # Model Performance KPIs
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Accuracy", f"{p_res.metrics['Accuracy']*100:.1f}%")
                        c2.metric("Precision", f"{p_res.metrics['Precision']*100:.1f}%")
                        c3.metric("Recall", f"{p_res.metrics['Recall']*100:.1f}%")
                        c4.metric("F1-Score", f"{p_res.metrics['F1']*100:.1f}%")

                        # Large Chart Area
                        if p_res.comparison_chart:
                            st.plotly_chart(p_res.comparison_chart, use_container_width=True)

                        # Key Insights Panel
                        st.markdown(
                            f"""
                            <div class="key-insights-card">
                                <div class="key-insights-title">💡 Classifier Performance Insights</div>
                                <div>{p_res.executive_summary}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        if p_res.feature_importance:
                            st.markdown("##### Top Predictive Feature Drivers")
                            fi_df = pd.DataFrame(list(p_res.feature_importance.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=False)
                            st.dataframe(fi_df, use_container_width=True)

                        # Interactive What-If Scenario Simulator for Classification
                        if p_res.trained_pipeline and p_res.features_used:
                            st.markdown('<div class="simulator-card">', unsafe_allow_html=True)
                            st.markdown("##### 🎛️ Interactive 'What-If' Scenario Simulator")
                            st.caption("Adjust input attributes below to observe real-time classification changes.")
                            sim_cols = p_res.features_used[:4]
                            sim_inputs = dict(p_res.default_feature_values)
                            sim_grid = st.columns(min(len(sim_cols), 4))
                            for s_i, sc in enumerate(sim_cols):
                                with sim_grid[s_i]:
                                    if sc in df.select_dtypes(include=[np.number]).columns:
                                        c_min = float(df[sc].min())
                                        c_max = float(df[sc].max())
                                        c_def = float(sim_inputs.get(sc, df[sc].median()))
                                        if c_min < c_max:
                                            sim_inputs[sc] = st.slider(f"{sc}", min_value=c_min, max_value=c_max, value=c_def, key=f"sim_cls_{sc}")
                                    else:
                                        u_vals = list(df[sc].dropna().unique())[:8]
                                        if u_vals:
                                            sim_inputs[sc] = st.selectbox(f"{sc}", u_vals, key=f"sim_cls_{sc}")

                            sim_out = DataPredictor.predict_what_if(p_res.trained_pipeline, sim_inputs)
                            if sim_out.get("success"):
                                st.info(f"🔮 **Predicted Class**: `{sim_out['prediction']}`")
                                if sim_out.get("probabilities"):
                                    prob_df = pd.DataFrame(list(sim_out["probabilities"].items()), columns=["Class", "Confidence (%)"])
                                    st.dataframe(prob_df, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                        with st.expander("⚠️ Limitations & Generalization Checks"):
                            for lim in p_res.limitations:
                                st.caption(f"• {lim}")
                    else:
                        st.error(p_res.error)
                else:
                    st.markdown(
                        """
                        <div class="empty-state-card">
                            <div class="empty-state-icon">🏷️</div>
                            <div class="empty-state-title">Ready for Classification Modeling</div>
                            <div class="empty-state-desc">Select your target category and architecture on the left, then click <b>Train Classification Model</b> to evaluate holdout performance and feature importance.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Tab 3: Regression
        with tab_reg:
            reg_col_cfg, reg_col_res = st.columns([1, 2.2])

            with reg_col_cfg:
                st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
                st.markdown("###### ⚙️ Regression Configuration")
                num_cols_reg = profile.numerical_columns
                t_col_reg = st.selectbox("Target Column (Numerical):", num_cols_reg, index=0 if num_cols_reg else 0, key="reg_target")
                m_type_reg = st.selectbox("Model Architecture:", ["random_forest", "gradient_boosting", "linear"], key="reg_arch")

                run_reg_btn = st.button("Train Regression Model", type="primary", use_container_width=True, key="run_reg_btn")
                st.markdown('</div>', unsafe_allow_html=True)

            with reg_col_res:
                if run_reg_btn:
                    with st.spinner("Training model with leakage-free holdout cross-validation..."):
                        p_res = DataPredictor.train_regression(df, target_col=t_col_reg, model_type=m_type_reg)
                        st.session_state.regression_model_res = p_res

                if st.session_state.get("regression_model_res"):
                    p_res = st.session_state.regression_model_res
                    if p_res.success:
                        st.success("✅ Model trained and evaluated on 20% holdout test set!")

                        # Model Performance KPIs
                        m1, m2, m3 = st.columns(3)
                        m1.metric("R² Score (Goodness of Fit)", f"{p_res.metrics['R2']:.3f}")
                        m2.metric("Mean Absolute Error (MAE)", f"{p_res.metrics['MAE']:,.2f}")
                        m3.metric("Root Mean Squared Error (RMSE)", f"{p_res.metrics['RMSE']:,.2f}")

                        # Large Chart Area
                        if p_res.comparison_chart:
                            st.plotly_chart(p_res.comparison_chart, use_container_width=True)

                        # Key Insights Panel
                        st.markdown(
                            f"""
                            <div class="key-insights-card">
                                <div class="key-insights-title">💡 Regression Model Insights</div>
                                <div>{p_res.executive_summary}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        if p_res.feature_importance:
                            st.markdown("##### Top Predictive Feature Drivers")
                            fi_df = pd.DataFrame(list(p_res.feature_importance.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=False)
                            st.dataframe(fi_df, use_container_width=True)

                        # Interactive What-If Scenario Simulator for Regression
                        if p_res.trained_pipeline and p_res.features_used:
                            st.markdown('<div class="simulator-card">', unsafe_allow_html=True)
                            st.markdown("##### 🎛️ Interactive 'What-If' Scenario Simulator")
                            st.caption("Adjust key drivers below to simulate predicted outcomes in real time.")
                            sim_cols = p_res.features_used[:4]
                            sim_inputs = dict(p_res.default_feature_values)
                            sim_grid = st.columns(min(len(sim_cols), 4))
                            for s_i, sc in enumerate(sim_cols):
                                with sim_grid[s_i]:
                                    if sc in df.select_dtypes(include=[np.number]).columns:
                                        c_min = float(df[sc].min())
                                        c_max = float(df[sc].max())
                                        c_def = float(sim_inputs.get(sc, df[sc].median()))
                                        if c_min < c_max:
                                            sim_inputs[sc] = st.slider(f"{sc}", min_value=c_min, max_value=c_max, value=c_def, key=f"sim_reg_{sc}")
                                    else:
                                        u_vals = list(df[sc].dropna().unique())[:8]
                                        if u_vals:
                                            sim_inputs[sc] = st.selectbox(f"{sc}", u_vals, key=f"sim_reg_{sc}")

                            sim_out = DataPredictor.predict_what_if(p_res.trained_pipeline, sim_inputs)
                            if sim_out.get("success"):
                                sim_pred = sim_out["prediction"]
                                base_mean = float(df[p_res.target_column].mean())
                                d_pct = ((sim_pred - base_mean) / base_mean * 100) if base_mean != 0 else 0.0

                                s_c1, s_c2 = st.columns(2)
                                with s_c1:
                                    st.metric(f"Simulated {p_res.target_column}", f"{sim_pred:,.2f}", delta=f"{d_pct:+.1f}% vs Dataset Mean")
                                with s_c2:
                                    g_fig = DataVisualizer.build_gauge_chart(
                                        value=float(sim_pred),
                                        min_val=float(df[p_res.target_column].min()),
                                        max_val=float(df[p_res.target_column].max()),
                                        target_val=float(base_mean),
                                        title="Simulated Output vs Baseline Mean"
                                    )
                                    st.plotly_chart(g_fig, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                        with st.expander("⚠️ Limitations & Uncertainty Considerations"):
                            for lim in p_res.limitations:
                                st.caption(f"• {lim}")
                    else:
                        st.error(p_res.error)
                else:
                    st.markdown(
                        """
                        <div class="empty-state-card">
                            <div class="empty-state-icon">🎯</div>
                            <div class="empty-state-title">Ready for Regression Modeling</div>
                            <div class="empty-state-desc">Select your numerical target metric and algorithm on the left, then click <b>Train Regression Model</b> to evaluate goodness-of-fit and simulate outcomes.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


# =============================================================
# 7. REPORTS & HISTORY (FILE EXPORTS & PDF REPORT)
# =============================================================
elif navigation == "📑 Reports & History":
    render_page_header(
        "Reports & History",
        "Generate comprehensive reports, download datasets in multiple formats, and review analytical audit trails."
    )

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home.")
    else:
        df = st.session_state.df
        profile = st.session_state.profile
        recs = RecommendationEngine.generate_recommendations(df, profile)

        r_tab1, r_tab2 = st.tabs(["📜 Analysis History", "📑 Saved Reports & Exports"])

        with r_tab1:
            hist_col_left, hist_col_right = st.columns([3, 2])

            with hist_col_left:
                st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
                st.markdown("###### 🕒 Analysis & Query Audit History")

                active_msgs = get_active_messages()
                history_rows = []
                for idx, m in enumerate(active_msgs):
                    if m["role"] == "user":
                        resp = active_msgs[idx+1] if idx + 1 < len(active_msgs) else {}
                        history_rows.append({
                            "#": len(history_rows) + 1,
                            "Query": m["content"][:45] + ("..." if len(m["content"]) > 45 else ""),
                            "Has Chart": "📊 Yes" if resp.get("figure") is not None else "—",
                            "Has Table": "📋 Yes" if resp.get("table") is not None else "—",
                            "Status": "✅ Verified" if not resp.get("has_error") else "⚠️ Error"
                        })

                if history_rows:
                    hist_df = pd.DataFrame(history_rows)
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)
                else:
                    st.markdown(
                        """
                        <div class="empty-state-card" style="padding: 1.5rem;">
                            <div class="empty-state-icon">📜</div>
                            <div class="empty-state-title">No Analysis History Yet</div>
                            <div class="empty-state-desc">Ask questions in <b>Ask AI</b> or execute transformations to populate your session history.</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("###### 💬 Saved Session Conversations")
                if st.session_state.conversations:
                    for cid, cinfo in st.session_state.conversations.items():
                        with st.expander(f"📁 {cinfo['title']} ({cinfo['created_at']}) • {len(cinfo['messages'])} msgs"):
                            for m in cinfo["messages"][-6:]:
                                st.caption(f"**{m['role'].capitalize()}**: {m['content'][:140]}...")
                st.markdown('</div>', unsafe_allow_html=True)

            with hist_col_right:
                st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
                st.markdown("###### 📄 Generate Executive Intelligence Report")
                st.caption("Configure report sections and compile a verified intelligence report.")

                inc_charts = st.checkbox("Include Visualizations & Charts", value=True, key="rep_inc_charts")
                inc_calcs = st.checkbox("Include Calculations & Formulas", value=True, key="rep_inc_calcs")
                inc_recs = st.checkbox("Include Strategic Recommendations", value=True, key="rep_inc_recs")
                inc_summary = st.checkbox("Include Executive Dataset Profile", value=True, key="rep_inc_summary")

                out_format = st.selectbox(
                    "Report Output Format:",
                    ["PDF Executive Document (.pdf)", "Excel Analytical Workbook (.xlsx)", "CSV Summary Archive (.csv)", "JSON Analysis Data (.json)"],
                    key="rep_format"
                )

                custom_notes = st.text_area(
                    "Executive Notes & Strategic Context (Optional):",
                    placeholder="Enter analyst commentary, strategic goals, or quarterly observations to include in the generated report...",
                    key="rep_notes",
                    height=100
                )

                if st.button("Generate & Download Report", type="primary", use_container_width=True, key="gen_rep_btn"):
                    with st.spinner("Compiling report with verified calculations and high-resolution layout..."):
                        if "PDF" in out_format:
                            pdf_bytes = PDFReportGenerator.generate_report(
                                df=df,
                                profile=profile,
                                recommendations=recs,
                                include_summary=inc_summary,
                                include_kpis=inc_calcs,
                                include_features=inc_charts,
                                include_recommendations=inc_recs,
                                custom_notes=custom_notes or None
                            )
                            st.download_button(
                                "📥 Download Executive PDF Report",
                                data=pdf_bytes,
                                file_name=f"{st.session_state.file_name.split('.')[0]}_Intelligence_Report.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="dl_pdf_rep"
                            )
                        elif "Excel" in out_format:
                            excel_bytes = DataExporter.to_excel_bytes(df)
                            st.download_button(
                                "📥 Download Excel Workbook (.xlsx)",
                                data=excel_bytes,
                                file_name=f"{st.session_state.file_name.split('.')[0]}_Analysis.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key="dl_xlsx_rep"
                            )
                        elif "CSV" in out_format:
                            csv_bytes = DataExporter.to_csv_bytes(df)
                            st.download_button(
                                "📥 Download CSV Dataset (.csv)",
                                data=csv_bytes,
                                file_name=f"{st.session_state.file_name.split('.')[0]}_Dataset.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key="dl_csv_rep"
                            )
                        else:
                            json_bytes = DataExporter.to_json_bytes(df)
                            st.download_button(
                                "📥 Download JSON Analysis (.json)",
                                data=json_bytes,
                                file_name=f"{st.session_state.file_name.split('.')[0]}_Dataset.json",
                                mime="application/json",
                                use_container_width=True,
                                key="dl_json_rep"
                            )
                        st.success("✅ Report generated successfully!")

                st.markdown('</div>', unsafe_allow_html=True)

        with r_tab2:
            st.markdown("##### 💾 Download Current Working Dataset")
            st.caption(f"Active working dataset: {len(df):,} rows × {len(df.columns)} columns")

            exp_c1, exp_c2, exp_c3 = st.columns(3)
            with exp_c1:
                csv_bytes = DataExporter.to_csv_bytes(df)
                st.download_button("📥 Export as CSV", data=csv_bytes, file_name="exported_dataset.csv", mime="text/csv", use_container_width=True, key="tab2_dl_csv")
            with exp_c2:
                excel_bytes = DataExporter.to_excel_bytes(df)
                st.download_button("📥 Export as Excel (XLSX)", data=excel_bytes, file_name="exported_dataset.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="tab2_dl_xlsx")
            with exp_c3:
                json_bytes = DataExporter.to_json_bytes(df)
                st.download_button("📥 Export as JSON", data=json_bytes, file_name="exported_dataset.json", mime="application/json", use_container_width=True, key="tab2_dl_json")

            st.markdown("---")
            st.markdown("##### 💡 Strategic Recommendations & Action Plan")
            for rec in recs.recommendations:
                p_badge = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}.get(rec.priority, rec.priority)
                st.markdown(
                    f"""
                    <div class="aha-ticker-card">
                        <div class="aha-ticker-header">
                            <span class="aha-ticker-title">{rec.title}</span>
                            <span class="aha-ticker-badge">{p_badge} • {rec.evidence_type}</span>
                        </div>
                        <div class="aha-ticker-desc">
                            <b>Observed Fact:</b> {rec.observation}<br/>
                            <b>Why It Matters:</b> {rec.why_it_matters}<br/>
                            <b>Suggested Next Step:</b> {rec.suggested_action}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# =============================================================
# 8. SETTINGS / ABOUT
# =============================================================
elif navigation == "⚙️ Settings / About":
    render_page_header(
        "Settings / About",
        "Configure API credentials, model inference parameters, and inspect system architecture."
    )

    col_cfg1, col_cfg2 = st.columns(2)

    with col_cfg1:
        st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
        st.markdown("##### 🔑 Groq API Configuration")
        user_key = st.text_input(
            "Groq API Key:",
            value=st.session_state.groq_api_key,
            type="password",
            help="Get your free API key at https://console.groq.com"
        )
        if user_key != st.session_state.groq_api_key:
            st.session_state.groq_api_key = user_key
            os.environ["GROQ_API_KEY"] = user_key

        model_choice = st.selectbox(
            "Select Model Architecture",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.selected_model) if st.session_state.selected_model in AVAILABLE_MODELS else 0
        )
        st.session_state.selected_model = model_choice

        if st.button("⚡ Test Groq Connection", type="secondary"):
            if LLMClient.is_available(st.session_state.groq_api_key):
                with st.spinner("Testing Groq API connection and latency..."):
                    test_res = LLMClient.test_connection(
                        explicit_key=st.session_state.groq_api_key,
                        model_name=st.session_state.selected_model
                    )
                    if test_res["success"]:
                        st.success(f"Groq API Connected! Latency: {test_res['latency_ms']}ms • Model: {test_res['model']}")
                    else:
                        st.error(f"Connection failed: {test_res.get('error')}")
            else:
                st.warning("Please provide a valid Groq API key starting with 'gsk_'.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="white-content-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown("##### 🎨 Active Color Theme — Blue & White")
        th_c1, th_c2, th_c3 = st.columns(3)
        with th_c1:
            st.markdown(f'<div style="background:{COLOR_PRIMARY}; color:#FFFFFF; padding:8px; border-radius:6px; text-align:center; font-weight:600;">Primary: {COLOR_PRIMARY}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:{COLOR_SIDEBAR_BG}; color:#FFFFFF; padding:8px; border-radius:6px; text-align:center; font-weight:600; margin-top:6px;">Sidebar: {COLOR_SIDEBAR_BG}</div>', unsafe_allow_html=True)
        with th_c2:
            st.markdown(f'<div style="background:{COLOR_DARK_BLUE}; color:#FFFFFF; padding:8px; border-radius:6px; text-align:center; font-weight:600;">Dark Blue: {COLOR_DARK_BLUE}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:{COLOR_LIGHT_BLUE}; color:{COLOR_DARK_BLUE}; padding:8px; border-radius:6px; text-align:center; font-weight:600; margin-top:6px;">Light Blue: {COLOR_LIGHT_BLUE}</div>', unsafe_allow_html=True)
        with th_c3:
            st.markdown(f'<div style="background:{COLOR_SUCCESS_BG}; color:{COLOR_SUCCESS}; padding:8px; border-radius:6px; text-align:center; font-weight:600;">Success: {COLOR_SUCCESS}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:#FEF3C7; color:{COLOR_WARNING}; padding:8px; border-radius:6px; text-align:center; font-weight:600; margin-top:6px;">Warning: {COLOR_WARNING}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cfg2:
        st.markdown('<div class="white-content-card">', unsafe_allow_html=True)
        st.markdown("##### 🛡️ Enterprise Security & Privacy")
        st.info(
            """
            **Deterministic Execution**:
            - All mathematical and statistical metrics computed via Pandas & NumPy.
            - Arbitrary code execution (`eval()`, `exec()`) is completely disallowed.
            - Derived formulas are parsed through an Abstract Syntax Tree (AST) validator.
            - Uploaded data is strictly isolated within the active Streamlit session state.
            """
        )

        st.markdown("##### 📦 System Diagnostics & Dependencies")
        d_c1, d_c2 = st.columns(2)
        with d_c1:
            st.caption(f"• Python: `{sys.version.split()[0]}`")
            st.caption(f"• Streamlit: `{st.__version__}`")
            st.caption(f"• Pandas: `{pd.__version__}`")
            st.caption(f"• NumPy: `{np.__version__}`")
        with d_c2:
            try:
                import sklearn
                st.caption(f"• Scikit-Learn: `{sklearn.__version__}`")
            except Exception:
                pass
            try:
                import plotly
                st.caption(f"• Plotly: `{plotly.__version__}`")
            except Exception:
                pass
            try:
                import langgraph
                st.caption(f"• LangGraph: `{langgraph.__version__}`")
            except Exception:
                pass
            try:
                import reportlab
                st.caption(f"• ReportLab: `{reportlab.__version__}`")
            except Exception:
                pass

        st.markdown("##### 📐 LangGraph Workflow Structure")
        st.code(
            """
[User Request]
       │
       ▼
[Understand Schema & Context] ──> (Groq JSON / Semantic Router / Pydantic)
       │
       ▼
[Execute Validated Tool]     ──> (Calculator | Visualizer | Predictor | Cleaner)
       │
       ▼
[Validate Tool Result]       ──> (Checks integrity & error bounds)
       │
       ▼
[Stream Synthesized Response] ──> (Token-by-token Natural Language Explanation)
            """,
            language="text"
        )
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# 9. MOBILE ASK AI (RESPONSIVE VIEW)
# =============================================================
elif navigation == "📱 Mobile Ask AI":
    # Compact mobile top bar matching reference view 9
    st.markdown(
        f"""
        <div class="mobile-chat-topbar">
            <div class="mobile-chat-title">
                <span style="font-size: 1.2rem;">💬</span>
                <span>InsightFlow AI</span>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="assistant-badge" style="font-size: 0.72rem; padding: 0.2rem 0.5rem;">
                    📁 {st.session_state.file_name or 'No Data'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    m_col1, m_col2 = st.columns([3, 1])
    with m_col1:
        st.caption("📱 Mobile Chat Experience • Optimized for compact viewports")
    with m_col2:
        if st.button("➕ New Chat", key="mob_chat_new_btn", use_container_width=True):
            create_new_conversation("Mobile Chat")
            st.rerun()

    if st.session_state.df is None:
        st.warning("Please upload or select a dataset first in Data Workspace or Home to begin analysis.")
    else:
        mob_active_messages = get_active_messages()
        mob_clicked_chip = None

        # Mobile welcome state
        if not mob_active_messages:
            st.markdown(
                """
                <div class="empty-state-card" style="padding: 1.25rem;">
                    <div class="empty-state-icon">🤖</div>
                    <div class="empty-state-title">InsightFlow Mobile Analyst</div>
                    <div class="empty-state-desc">Ask any question about your data below to receive instant formulas, charts, and executive insights.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            cards = get_default_prompt_cards(st.session_state.profile)
            for idx, c in enumerate(cards[:2]):
                if st.button(f"{c['icon']} {c['title']}: {c['prompt']}", key=f"mob_pcard_{idx}", use_container_width=True):
                    mob_clicked_chip = c["prompt"]

        # Render conversation messages in responsive single column
        for i, msg in enumerate(mob_active_messages):
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="📊"):
                    st.markdown('<div class="assistant-badge">● InsightFlow Analyst</div>', unsafe_allow_html=True)
                    st.markdown(msg["content"])

                    if msg.get("formula"):
                        st.markdown(f'<div class="formula-pill">Formula: {msg["formula"]}</div>', unsafe_allow_html=True)

                    if msg.get("table") is not None:
                        with st.expander("📊 View Data Table", expanded=True):
                            mob_tbl = msg["table"]
                            st.dataframe(mob_tbl.head(10), use_container_width=True)
                            mob_csv = DataExporter.to_csv_bytes(mob_tbl)
                            st.download_button("📥 Download Table (CSV)", data=mob_csv, file_name="table.csv", mime="text/csv", key=f"mob_dl_tbl_{i}")

                    if msg.get("figure") is not None:
                        st.plotly_chart(msg["figure"], use_container_width=True)

                    if msg.get("insights"):
                        st.markdown(
                            f"""
                            <div class="key-insights-card">
                                <div class="key-insights-title">💡 Key Insights</div>
                                <div>{msg['insights']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        # Dynamic follow-up chips
        if mob_active_messages and mob_active_messages[-1]["role"] == "assistant":
            last_u = ""
            for m in reversed(mob_active_messages):
                if m["role"] == "user":
                    last_u = m["content"]
                    break
            fup = get_follow_up_action_chips(last_u, st.session_state.profile)
            if fup:
                st.markdown("###### ⚡ Follow-up Actions")
                for f_i, fc in enumerate(fup[:2]):
                    if st.button(fc["label"], key=f"mob_fup_{f_i}_{len(mob_active_messages)}", use_container_width=True):
                        mob_clicked_chip = fc["query"]

        # Mobile input composer anchored at bottom
        mob_user_input = st.chat_input("Ask about your data on mobile...", key="mob_chat_input")
        mob_query = mob_clicked_chip or mob_user_input

        if mob_query:
            mob_active_messages.append({"role": "user", "content": mob_query})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(mob_query)

            with st.chat_message("assistant", avatar="📊"):
                st.markdown('<div class="assistant-badge">● InsightFlow Analyst</div>', unsafe_allow_html=True)

                with st.spinner("Analyzing schema & executing deterministic calculation..."):
                    stream_iter, meta = AnalystAgent.run_stream(
                        query=mob_query,
                        df=st.session_state.df,
                        profile=st.session_state.profile,
                        chat_history=mob_active_messages,
                        api_key=st.session_state.groq_api_key,
                        model_name=st.session_state.selected_model
                    )

                full_resp = st.write_stream(stream_iter)

                if meta.get("formula"):
                    st.markdown(f'<div class="formula-pill">Formula: {meta["formula"]}</div>', unsafe_allow_html=True)

                if meta.get("table") is not None:
                    with st.expander("📊 View Data Table", expanded=True):
                        st.dataframe(meta["table"].head(10), use_container_width=True)
                        c_b = DataExporter.to_csv_bytes(meta["table"])
                        st.download_button("📥 Download Table", data=c_b, file_name="table.csv", mime="text/csv", key=f"mob_stream_tbl_{len(mob_active_messages)}")

                if meta.get("figure") is not None:
                    st.plotly_chart(meta["figure"], use_container_width=True)

            mob_active_messages.append({
                "role": "assistant",
                "content": full_resp,
                "formula": meta.get("formula"),
                "figure": meta.get("figure"),
                "table": meta.get("table"),
                "has_error": not meta.get("success", True)
            })

            if len(mob_active_messages) <= 2:
                st.session_state.conversations[st.session_state.active_conv_id]["title"] = mob_query[:25]

