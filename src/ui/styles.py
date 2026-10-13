"""Master design system and SaaS CSS styling tokens for InsightFlow AI (Blue and White Theme)."""
from src.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_DARK_BLUE,
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_EXACT_BG, COLOR_SIDEBAR_SECONDARY,
    COLOR_SIDEBAR_ACTIVE, COLOR_SIDEBAR_ACTIVE_HOVER, COLOR_SIDEBAR_NAV_HOVER,
    COLOR_SIDEBAR_INACTIVE_TEXT, COLOR_SIDEBAR_INACTIVE_ICON,
    COLOR_SIDEBAR_SUBTITLE, COLOR_SIDEBAR_DIVIDER,
    COLOR_SIDEBAR_GRADIENT_END,
    COLOR_LIGHT_BLUE, COLOR_PALE_BLUE, COLOR_MAIN_BG,
    COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_SUCCESS, COLOR_SUCCESS_BG,
    COLOR_WARNING, COLOR_ERROR,
    SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH
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
   Master Dark Navy Sidebar Specification ({COLOR_SIDEBAR_EXACT_BG})
------------------------------------------------------------- */
section[data-testid="stSidebar"] {{
    background-color: {COLOR_SIDEBAR_EXACT_BG} !important;
    background: {COLOR_SIDEBAR_EXACT_BG} !important;
    border-right: 1px solid {COLOR_SIDEBAR_SECONDARY} !important;
    width: {SIDEBAR_EXPANDED_WIDTH}px !important;
    min-width: {SIDEBAR_EXPANDED_WIDTH}px !important;
    transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

/* Hide native empty sidebar header in modern Streamlit */
section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"] {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {{
    background-color: {COLOR_SIDEBAR_EXACT_BG} !important;
    background: {COLOR_SIDEBAR_EXACT_BG} !important;
    padding: 0 !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {{
    display: flex !important;
    flex-direction: column !important;
    min-height: 100vh !important;
    height: 100vh !important;
    padding: 0.75rem 0.85rem 0.85rem 0.85rem !important;
    box-sizing: border-box !important;
    background: {COLOR_SIDEBAR_EXACT_BG} !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}}

/* Direct top-level sidebar vertical block */
section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    min-height: calc(100vh - 1.8rem) !important;
    gap: 4px !important;
}}

/* Sidebar columns (top branding row) must NOT stretch or have auto top margin */
section[data-testid="stSidebar"] div[data-testid="stColumns"],
section[data-testid="stSidebar"] div[data-testid="column"],
section[data-testid="stSidebar"] div[data-testid="column"] div[data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] div[data-testid="column"] div[data-testid="stVerticalBlockBorderWrapper"] > div {{
    min-height: unset !important;
    height: auto !important;
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
}}

section[data-testid="stSidebar"] div[data-testid="column"] div[data-testid="stVerticalBlock"] > div {{
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}}

section[data-testid="stSidebar"] div[data-testid="stElementContainer"],
section[data-testid="stSidebar"] div[data-testid="element-container"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

/* Bottom profile container anchored at the bottom */
.sidebar-bottom-profile {{
    margin-top: auto !important;
    width: 100% !important;
    padding-top: 0.4rem !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] > div:has(.sidebar-bottom-profile) {{
    margin-top: auto !important;
    width: 100% !important;
}}

section[data-testid="stSidebar"] .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

/* Sidebar Collapse Toggle Button (◀) */
section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button {{
    width: 34px !important;
    min-width: 34px !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background-color: {COLOR_SIDEBAR_SECONDARY} !important;
    color: #B7CBE5 !important;
    border: 1px solid {COLOR_SIDEBAR_DIVIDER} !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}}

section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button:hover {{
    background-color: {COLOR_SIDEBAR_ACTIVE} !important;
    color: #FFFFFF !important;
    border-color: {COLOR_SIDEBAR_ACTIVE} !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
}}

section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button p,
section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button span {{
    color: #B7CBE5 !important;
    font-size: 13px !important;
    line-height: 1 !important;
    margin: 0 !important;
}}

section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button:hover p,
section[data-testid="stSidebar"] div.st-key-sidebar_collapse_toggle button:hover span {{
    color: #FFFFFF !important;
}}

/* Sidebar Expand / Open Button (▶) when collapsed */
section[data-testid="stSidebar"] div.st-key-sidebar_expand_toggle button {{
    width: 44px !important;
    min-width: 44px !important;
    height: 40px !important;
    min-height: 40px !important;
    margin: 4px auto 10px auto !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: 1.5px solid #60A5FA !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45) !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

section[data-testid="stSidebar"] div.st-key-sidebar_expand_toggle button:hover {{
    background: #2563EB !important;
    color: #FFFFFF !important;
    border-color: #93C5FD !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.65) !important;
    transform: scale(1.08) !important;
}}

section[data-testid="stSidebar"] div.st-key-sidebar_expand_toggle button p,
section[data-testid="stSidebar"] div.st-key-sidebar_expand_toggle button span {{
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 700 !important;
}}

/* Streamlit Native Collapsed Control (Reopen Sidebar Button) */
[data-testid="collapsedControl"],
div[data-testid="collapsedControl"] button,
button[data-testid="stSidebarCollapseButton"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #0B2545 !important;
    color: #FFFFFF !important;
    border: 1.5px solid #2563EB !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.45) !important;
    top: 14px !important;
    left: 14px !important;
    width: 42px !important;
    height: 42px !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 999999 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

[data-testid="collapsedControl"]:hover,
div[data-testid="collapsedControl"] button:hover,
button[data-testid="stSidebarCollapseButton"]:hover {{
    background: #2563EB !important;
    border-color: #60A5FA !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.65) !important;
    transform: scale(1.06) !important;
}}

[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] span,
div[data-testid="collapsedControl"] button svg {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}}

/* Sidebar Branding Header */
.sidebar-branding-box {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 0.85rem;
    padding: 0.1rem 0;
}}

.sidebar-branding-logo {{
    width: 52px;
    height: 52px;
    min-width: 52px;
    background-color: {COLOR_SIDEBAR_ACTIVE};
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.sidebar-branding-logo:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.45);
}}

.sidebar-branding-text {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}}

.sidebar-branding-title {{
    font-size: 21px;
    font-weight: 700;
    color: #FFFFFF !important;
    letter-spacing: -0.025em;
    line-height: 1.2;
    margin: 0;
    white-space: nowrap !important;
}}

.sidebar-branding-subtitle {{
    font-size: 13px;
    font-weight: 500;
    color: {COLOR_SIDEBAR_SUBTITLE} !important;
    margin-top: 3px;
    letter-spacing: -0.01em;
    line-height: 1.2;
    white-space: nowrap !important;
}}

/* Sidebar Navigation Buttons */
section[data-testid="stSidebar"] button {{
    background-color: transparent !important;
    background: transparent !important;
    color: {COLOR_SIDEBAR_INACTIVE_TEXT} !important;
    border: none !important;
    border-radius: 10px !important;
    height: 48px !important;
    min-height: 48px !important;
    padding: 0 14px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 13px !important;
    font-size: 15.5px !important;
    font-weight: 500 !important;
    letter-spacing: -0.015em !important;
    box-shadow: none !important;
    transition: background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease !important;
    cursor: pointer !important;
    box-sizing: border-box !important;
    width: 100% !important;
    text-align: left !important;
}}

/* Inactive Navigation Item Hover */
section[data-testid="stSidebar"] button:hover {{
    background-color: {COLOR_SIDEBAR_NAV_HOVER} !important;
    background: {COLOR_SIDEBAR_NAV_HOVER} !important;
    color: #FFFFFF !important;
    border: none !important;
}}

section[data-testid="stSidebar"] button p,
section[data-testid="stSidebar"] button span {{
    color: {COLOR_SIDEBAR_INACTIVE_TEXT} !important;
}}

section[data-testid="stSidebar"] button:hover p,
section[data-testid="stSidebar"] button:hover span {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] button span[data-testid="stIconMaterial"] {{
    font-size: 26px !important;
    width: 26px !important;
    height: 26px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    margin: 0 !important;
    color: {COLOR_SIDEBAR_INACTIVE_ICON} !important;
}}

section[data-testid="stSidebar"] button:hover span[data-testid="stIconMaterial"] {{
    color: #FFFFFF !important;
}}

/* Active Navigation Item: Bright Blue (#2563EB) Rounded Pill */
section[data-testid="stSidebar"] button[kind="primary"],
section[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {{
    background-color: {COLOR_SIDEBAR_ACTIVE} !important;
    background: {COLOR_SIDEBAR_ACTIVE} !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
}}

section[data-testid="stSidebar"] button[kind="primary"]:hover,
section[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {{
    background-color: {COLOR_SIDEBAR_ACTIVE_HOVER} !important;
    background: {COLOR_SIDEBAR_ACTIVE_HOVER} !important;
    border: none !important;
}}

section[data-testid="stSidebar"] button[kind="primary"] p,
section[data-testid="stSidebar"] button[kind="primary"] span {{
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] button[kind="primary"] span[data-testid="stIconMaterial"] {{
    color: #FFFFFF !important;
    font-size: 26px !important;
}}

/* Typography alignment inside navigation buttons */
section[data-testid="stSidebar"] button div[data-testid="stMarkdownContainer"] {{
    line-height: 1 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

section[data-testid="stSidebar"] button div[data-testid="stMarkdownContainer"] p {{
    font-size: 16.5px !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

/* Sidebar Toggle Buttons (◀ and ▶) */
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-of-type button {{
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: {COLOR_SIDEBAR_SUBTITLE} !important;
    font-size: 14px !important;
    height: 36px !important;
    min-height: 36px !important;
    width: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    border-radius: 9px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 10px auto 0 auto !important;
    transition: all 0.18s ease !important;
}}

section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-of-type button:hover {{
    background: {COLOR_SIDEBAR_NAV_HOVER} !important;
    border-color: {COLOR_SIDEBAR_ACTIVE} !important;
    color: #FFFFFF !important;
}}

/* -------------------------------------------------------------
   Bottom Profile Section (Anchored via flex margin-top: auto)
/* Fix Side Image Bug: Streamlit Native Collapsed Control Reset */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"] {{
    display: none !important;
}}

/* -------------------------------------------------------------
   Google Sign-In & Authenticated User Profile (Bottom Sidebar)
------------------------------------------------------------- */
.sidebar-bottom-profile {{
    margin-top: auto !important;
    padding-top: 0.75rem !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}

.sidebar-profile-divider {{
    height: 1px !important;
    width: 100% !important;
    background-color: {COLOR_SIDEBAR_DIVIDER} !important;
    margin-bottom: 0.75rem !important;
    opacity: 0.9 !important;
}}

/* Logged-out Google Sign-in Card */
.google-signin-container {{
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    width: 100% !important;
}}

.google-signin-btn {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 10px !important;
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #1F2937 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 9px !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 14px !important;
    font-size: 14.5px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    cursor: pointer !important;
    transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}

.google-signin-btn:hover {{
    background-color: #F9FAFB !important;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15) !important;
    transform: translateY(-1px) !important;
    color: #111827 !important;
}}

.google-signin-btn span {{
    color: #1F2937 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}

.google-signin-caption {{
    font-size: 12px !important;
    color: {COLOR_SIDEBAR_SUBTITLE} !important;
    text-align: center !important;
    margin-top: 2px !important;
    letter-spacing: -0.01em !important;
}}

/* Clean Dual Login Buttons (Guest & Google) */
.sidebar-guest-btn button,
section[data-testid="stSidebar"] div.sidebar-guest-btn button,
section[data-testid="stSidebar"] div.sidebar-guest-btn div[data-testid="stButton"] > button {{
    background: rgba(30, 58, 138, 0.4) !important;
    background-color: rgba(30, 58, 138, 0.4) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 9px !important;
    height: 44px !important;
    min-height: 44px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}}

.sidebar-guest-btn button:hover,
section[data-testid="stSidebar"] div.sidebar-guest-btn button:hover {{
    background: rgba(37, 99, 235, 0.55) !important;
    background-color: rgba(37, 99, 235, 0.55) !important;
    border-color: #3B82F6 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}}

.sidebar-guest-btn button p,
.sidebar-guest-btn button span,
section[data-testid="stSidebar"] div.sidebar-guest-btn button p,
section[data-testid="stSidebar"] div.sidebar-guest-btn button span {{
    color: #FFFFFF !important;
    font-weight: 600 !important;
}}

.sidebar-google-btn button,
section[data-testid="stSidebar"] div.sidebar-google-btn button,
section[data-testid="stSidebar"] div.sidebar-google-btn div[data-testid="stButton"] > button {{
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    color: #1F2937 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 9px !important;
    height: 44px !important;
    min-height: 44px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    width: 100% !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.2s ease !important;
}}

.sidebar-google-btn button:hover,
section[data-testid="stSidebar"] div.sidebar-google-btn button:hover {{
    background-color: #F9FAFB !important;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15) !important;
    transform: translateY(-1px) !important;
}}

.sidebar-google-btn button::before {{
    content: "" !important;
    display: inline-block !important;
    width: 18px !important;
    height: 18px !important;
    margin-right: 6px !important;
    background-repeat: no-repeat !important;
    background-size: contain !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%234285F4' d='M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z'/%3E%3Cpath fill='%2334A853' d='M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z'/%3E%3Cpath fill='%23FBBC05' d='M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z'/%3E%3Cpath fill='%23EA4335' d='M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z'/%3E%3C/svg%3E") !important;
}}

.sidebar-google-btn button p,
.sidebar-google-btn button span,
section[data-testid="stSidebar"] div.sidebar-google-btn button p,
section[data-testid="stSidebar"] div.sidebar-google-btn button span {{
    color: #1F2937 !important;
    font-weight: 600 !important;
}}


/* Sidebar Popover Button Styling */
section[data-testid="stSidebar"] div[data-testid="stPopover"] > button {{
    background-color: rgba(16, 47, 85, 0.8) !important;
    background: rgba(16, 47, 85, 0.8) !important;
    color: #FFFFFF !important;
    border: 1px solid {COLOR_SIDEBAR_DIVIDER} !important;
    border-radius: 10px !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 12px !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    justify-content: space-between !important;
    box-shadow: none !important;
    transition: background-color 0.18s ease, border-color 0.18s ease !important;
}}

section[data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover {{
    background-color: {COLOR_SIDEBAR_NAV_HOVER} !important;
    border-color: {COLOR_SIDEBAR_ACTIVE} !important;
}}

section[data-testid="stSidebar"] div[data-testid="stPopover"] > button p,
section[data-testid="stSidebar"] div[data-testid="stPopover"] > button span {{
    color: #FFFFFF !important;
}}

/* Authenticated Profile Card */
.sidebar-profile-card {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 0.35rem 0.3rem !important;
    border-radius: 11px !important;
    transition: background-color 0.15s ease !important;
    cursor: pointer !important;
    text-decoration: none !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}

.sidebar-profile-card:hover {{
    background-color: rgba(22, 59, 99, 0.5) !important;
}}

.sidebar-profile-avatar {{
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    border-radius: 50% !important;
    background: {COLOR_SIDEBAR_ACTIVE} !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
    overflow: hidden !important;
    border: 1.5px solid rgba(255, 255, 255, 0.2) !important;
}}

.sidebar-profile-avatar img {{
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
}}

.sidebar-profile-avatar-initials {{
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
}}

.sidebar-profile-info {{
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    flex: 1 !important;
    min-width: 0 !important;
}}

.sidebar-profile-name {{
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
    letter-spacing: -0.01em !important;
    line-height: 1.25 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.sidebar-profile-role {{
    font-size: 12.5px !important;
    font-weight: 400 !important;
    color: {COLOR_SIDEBAR_SUBTITLE} !important;
    margin-top: 2px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

.sidebar-profile-chevron {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: {COLOR_SIDEBAR_SUBTITLE} !important;
    padding-right: 2px !important;
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

/* Primary Buttons in Main Content */
.main button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    border-color: {COLOR_PRIMARY} !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease-in-out !important;
}}

.main button[kind="primary"]:hover {{
    background-color: {COLOR_PRIMARY_HOVER} !important;
    border-color: {COLOR_PRIMARY_HOVER} !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
}}

/* Secondary Buttons in Main Content */
.main button[kind="secondary"] {{
    background-color: {COLOR_MAIN_BG} !important;
    border: 1px solid {COLOR_BORDER} !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}}

.main button[kind="secondary"]:hover {{
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
