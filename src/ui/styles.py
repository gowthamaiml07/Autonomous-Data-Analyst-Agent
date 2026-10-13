"""Master design system and SaaS CSS styling tokens for InsightFlow AI (Blue and White Theme)."""
from src.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_DARK_BLUE,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_GRADIENT_END,
    COLOR_LIGHT_BLUE, COLOR_PALE_BLUE, COLOR_MAIN_BG,
    COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_SUCCESS, COLOR_SUCCESS_BG,
    COLOR_WARNING, COLOR_ERROR
)

CUSTOM_CSS = f"""
<style>
/* -------------------------------------------------------------
   Typography & Main Layout Reset
------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {COLOR_TEXT_PRIMARY};
}}

.main {{
    background-color: {COLOR_MAIN_BG};
}}

.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 4rem;
    max-width: 1320px;
}}

/* -------------------------------------------------------------
   Dark Navy Sidebar Styling
------------------------------------------------------------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {COLOR_SIDEBAR_BG} 0%, {COLOR_SIDEBAR_GRADIENT_END} 100%) !important;
    border-right: 1px solid #1E3A5F !important;
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem;
}}

.sidebar-brand-box {{
    padding: 0.6rem 0.2rem;
    margin-bottom: 0.8rem;
}}

.sidebar-brand-title {{
    font-size: 1.35rem;
    font-weight: 700;
    color: #FFFFFF !important;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    letter-spacing: -0.02em;
    margin: 0;
}}

.sidebar-brand-sub {{
    font-size: 0.78rem;
    color: #94A3B8 !important;
    margin-top: 0.25rem;
    font-weight: 500;
}}

/* Sidebar radio buttons (Navigation) */
section[data-testid="stSidebar"] div[data-testid="stRadio"] {{
    color: #F8FAFC !important;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {{
    color: #94A3B8 !important;
    font-size: 0.76rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 600 !important;
    margin-bottom: 0.4rem !important;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {{
    gap: 0.25rem !important;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] {{
    background: transparent;
    padding: 0.45rem 0.75rem;
    border-radius: 8px;
    margin: 0;
    transition: all 0.15s ease-in-out;
    cursor: pointer;
    border: 1px solid transparent;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {{
    background: rgba(37, 99, 235, 0.15) !important;
    border-color: rgba(37, 99, 235, 0.3) !important;
}}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] * {{
    color: #F1F5F9 !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}}

/* Sidebar horizontal rule */
section[data-testid="stSidebar"] hr {{
    border-color: #1E3A5F !important;
    margin: 0.9rem 0 !important;
}}

/* Sidebar dataset info widget */
.sidebar-dataset-card {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.75rem;
}}

.sidebar-dataset-title {{
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #94A3B8;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
}}

.sidebar-dataset-name {{
    font-size: 0.88rem;
    font-weight: 600;
    color: #FFFFFF;
    word-break: break-all;
}}

.sidebar-dataset-meta {{
    font-size: 0.78rem;
    color: #CBD5E1;
    margin-top: 0.2rem;
}}

/* Sidebar buttons */
section[data-testid="stSidebar"] button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    border-color: {COLOR_PRIMARY} !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
}}

section[data-testid="stSidebar"] button[kind="primary"]:hover {{
    background-color: {COLOR_PRIMARY_HOVER} !important;
    border-color: {COLOR_PRIMARY_HOVER} !important;
}}

section[data-testid="stSidebar"] button[kind="secondary"] {{
    background-color: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}}

section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
    background-color: rgba(37, 99, 235, 0.25) !important;
    border-color: {COLOR_PRIMARY} !important;
}}

/* Sidebar typography */
section[data-testid="stSidebar"] h6,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] p {{
    color: #CBD5E1 !important;
}}

/* -------------------------------------------------------------
   Header Structure (Crisp, Non-Oversized SaaS Header)
------------------------------------------------------------- */
.page-header-box {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0 1.2rem 0;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid {COLOR_BORDER};
}}

.page-title {{
    font-size: 1.65rem;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY} !important;
    margin: 0;
    letter-spacing: -0.025em;
    line-height: 1.25;
}}

.page-subtitle {{
    font-size: 0.88rem;
    color: {COLOR_TEXT_SECONDARY} !important;
    margin-top: 0.25rem;
    font-weight: 400;
}}

.page-header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.8rem;
    background: {COLOR_PALE_BLUE};
    border: 1px solid {COLOR_LIGHT_BLUE};
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    color: {COLOR_DARK_BLUE};
}}

/* Backward-compatible banner */
.saas-header-banner {{
    background: {COLOR_MAIN_BG};
    border: 1px solid {COLOR_BORDER};
    padding: 1.2rem 1.6rem;
    border-radius: 12px;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}}

.saas-header-title {{
    font-size: 1.5rem;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY} !important;
    margin: 0;
}}

.saas-header-sub {{
    font-size: 0.88rem;
    color: {COLOR_TEXT_SECONDARY} !important;
    margin-top: 0.25rem;
}}

/* Sidebar user profile at the bottom */
.sidebar-user-footer {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0.6rem;
    border-top: 1px solid #1E3A5F;
    margin-top: 1rem;
}}

.sidebar-user-avatar {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: rgba(37, 99, 235, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: #FFFFFF;
}}

.sidebar-user-name {{
    font-size: 0.84rem;
    font-weight: 600;
    color: #FFFFFF;
    line-height: 1.2;
}}

.sidebar-user-role {{
    font-size: 0.72rem;
    color: #94A3B8;
}}

/* Dataset Information Bar */
.dataset-info-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: {COLOR_SECONDARY_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
    padding: 0.75rem 1.15rem;
    margin-bottom: 1.2rem;
}}

.dataset-info-left {{
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}}

.dataset-info-filename {{
    font-size: 0.95rem;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
}}

.dataset-info-meta {{
    font-size: 0.82rem;
    color: {COLOR_TEXT_SECONDARY};
}}

/* Content Card Containers */
.white-content-card {{
    background: {COLOR_MAIN_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 1rem;
}}

.content-card-title {{
    font-size: 1rem;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
    margin-bottom: 0.4rem;
}}

.content-card-desc {{
    font-size: 0.84rem;
    color: {COLOR_TEXT_SECONDARY};
    margin-bottom: 0.85rem;
}}

/* Recent dataset item */
.recent-dataset-item {{
    background: {COLOR_MAIN_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    transition: all 0.15s ease;
}}

.recent-dataset-item:hover {{
    border-color: {COLOR_PRIMARY};
    background: {COLOR_PALE_BLUE};
}}

/* -------------------------------------------------------------
   KPI Cards (White Cards, Subtle Borders, Blue Accent)
------------------------------------------------------------- */
.kpi-card {{
    background: {COLOR_MAIN_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}}

.kpi-card:hover {{
    border-color: {COLOR_PRIMARY};
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.10);
    transform: translateY(-2px);
}}

.kpi-title {{
    font-size: 0.76rem;
    font-weight: 600;
    color: {COLOR_TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.35rem;
}}

.kpi-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY};
    margin: 0;
    line-height: 1.2;
}}

.kpi-sub {{
    font-size: 0.78rem;
    color: {COLOR_PRIMARY};
    margin-top: 0.3rem;
    font-weight: 500;
}}

/* -------------------------------------------------------------
   ChatGPT-Style Chat Elements
------------------------------------------------------------- */
.chat-welcome-container {{
    text-align: center;
    padding: 3rem 1rem 2rem 1rem;
}}

.chat-welcome-title {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {COLOR_TEXT_PRIMARY};
    margin-bottom: 0.5rem;
    letter-spacing: -0.02em;
}}

.chat-welcome-subtitle {{
    font-size: 1rem;
    color: {COLOR_TEXT_SECONDARY};
    margin-bottom: 2rem;
}}

.prompt-card {{
    background: {COLOR_MAIN_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    height: 100%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}

.prompt-card:hover {{
    border-color: {COLOR_PRIMARY};
    background: {COLOR_PALE_BLUE};
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
    transform: translateY(-2px);
}}

.prompt-card-icon {{
    font-size: 1.3rem;
    margin-bottom: 0.4rem;
}}

.prompt-card-text {{
    font-size: 0.88rem;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
    margin-bottom: 0.2rem;
}}

.prompt-card-desc {{
    font-size: 0.78rem;
    color: {COLOR_TEXT_SECONDARY};
}}

.assistant-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.65rem;
    background: {COLOR_PALE_BLUE};
    border: 1px solid {COLOR_LIGHT_BLUE};
    color: {COLOR_DARK_BLUE};
    font-size: 0.74rem;
    font-weight: 600;
    border-radius: 9999px;
    margin-bottom: 0.6rem;
}}

.formula-pill {{
    background: {COLOR_PALE_BLUE};
    border: 1px solid {COLOR_LIGHT_BLUE};
    color: {COLOR_DARK_BLUE};
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    display: inline-block;
    margin: 0.4rem 0;
}}

/* -------------------------------------------------------------
   Badges & Indicators
------------------------------------------------------------- */
.status-badge-active {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: {COLOR_SUCCESS_BG};
    color: {COLOR_SUCCESS};
    border: 1px solid #86EFAC;
}}

.status-badge-offline {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: #FEF3C7;
    color: {COLOR_WARNING};
    border: 1px solid #FDE68A;
}}

/* -------------------------------------------------------------
   Clean Data Tables & UI Controls
------------------------------------------------------------- */
.dataframe th {{
    background-color: {COLOR_SECONDARY_BG} !important;
    color: {COLOR_TEXT_SECONDARY} !important;
    font-weight: 600 !important;
}}

/* Primary Buttons */
button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    border-color: {COLOR_PRIMARY} !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease-in-out !important;
}}

button[kind="primary"]:hover {{
    background-color: {COLOR_PRIMARY_HOVER} !important;
    border-color: {COLOR_PRIMARY_HOVER} !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
}}

/* Secondary Buttons */
button[kind="secondary"] {{
    background-color: {COLOR_MAIN_BG} !important;
    border: 1px solid {COLOR_BORDER} !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}}

button[kind="secondary"]:hover {{
    background-color: {COLOR_PALE_BLUE} !important;
    border-color: {COLOR_PRIMARY} !important;
    color: {COLOR_PRIMARY} !important;
}}

/* Action Chips */
.action-chips-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.6rem;
    margin-bottom: 0.6rem;
}}

.action-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.75rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 500;
    color: {COLOR_PRIMARY};
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: all 0.15s ease-in-out;
}}

.action-chip:hover {{
    background: {COLOR_PALE_BLUE};
    border-color: {COLOR_PRIMARY};
    color: {COLOR_DARK_BLUE};
    transform: translateY(-1px);
}}

/* Aha Moments / Proactive Insights Cards */
.aha-ticker-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid {COLOR_PRIMARY};
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
}}

.aha-ticker-card:hover {{
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.09);
    border-color: {COLOR_PRIMARY};
    transform: translateY(-1px);
}}

.aha-ticker-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.35rem;
}}

.aha-ticker-title {{
    font-size: 0.88rem;
    font-weight: 600;
    color: #111827;
}}

.aha-ticker-badge {{
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 9999px;
    background: {COLOR_LIGHT_BLUE};
    color: {COLOR_DARK_BLUE};
}}

.aha-ticker-desc {{
    font-size: 0.8rem;
    color: #475569;
    line-height: 1.4;
}}

/* Quick Action Cards (Home Page) */
.quick-action-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.15rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
    height: 100%;
}}

.quick-action-card:hover {{
    border-color: {COLOR_PRIMARY};
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.08);
    transform: translateY(-2px);
}}

.quick-action-icon {{
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}}

.quick-action-title {{
    font-size: 1rem;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
    margin-bottom: 0.25rem;
}}

.quick-action-desc {{
    font-size: 0.82rem;
    color: {COLOR_TEXT_SECONDARY};
    line-height: 1.4;
}}

/* What-If Simulator Card */
.simulator-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}}

/* Clean up Streamlit header & footer */
#MainMenu {{visibility: visible;}}
footer {{visibility: hidden;}}
header {{visibility: visible;}}

/* Key Insights Panel */
.key-insights-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #2563EB;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}}

.key-insights-title {{
    font-size: 0.92rem;
    font-weight: 700;
    color: #111827;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.5rem;
}}

/* Mobile Ask AI Top Bar */
.mobile-chat-topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 0.85rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}}

.mobile-chat-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: #111827;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}

/* Tab highlight styling */
div[data-baseweb="tab-highlight"] {{
    background-color: #2563EB !important;
}}

div[data-baseweb="tab-list"] button[aria-selected="true"] {{
    color: #2563EB !important;
    font-weight: 600 !important;
}}
</style>
"""
