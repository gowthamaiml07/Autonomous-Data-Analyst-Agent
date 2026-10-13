"""Configuration, color tokens, and model settings for DataPilot AI."""
import os
from dataclasses import dataclass

# App branding and metadata
APP_TITLE = "DataPilot AI"
APP_SUBTITLE = "Autonomous Data Analyst Agent"
APP_ICON = "📊"
VERSION = "2.0.0"

# -------------------------------------------------------------
# Master Design Palette — Exact Dark Navy Sidebar & Blue/White SaaS Theme
# -------------------------------------------------------------
COLOR_PRIMARY = "#2563EB"              # Primary blue
COLOR_PRIMARY_HOVER = "#1D4ED8"        # Primary hover
COLOR_DARK_BLUE = "#1E40AF"            # Dark blue
COLOR_SIDEBAR_BG = "#0B2545"           # Main sidebar dark navy background (Exact reference)
COLOR_SIDEBAR_EXACT_BG = "#0B2545"     # Main sidebar background
COLOR_SIDEBAR_SECONDARY = "#102F55"    # Secondary navy
COLOR_SIDEBAR_ACTIVE = "#2563EB"       # Active navigation background
COLOR_SIDEBAR_ACTIVE_HOVER = "#1D4ED8" # Active navigation hover
COLOR_SIDEBAR_NAV_HOVER = "#163B63"    # Inactive navigation hover
COLOR_SIDEBAR_INACTIVE_TEXT = "#E5EEF9"# Inactive navigation text
COLOR_SIDEBAR_INACTIVE_ICON = "#D6E6FA"# Inactive icons
COLOR_SIDEBAR_SUBTITLE = "#B7CBE5"     # Sidebar subtitle
COLOR_SIDEBAR_DIVIDER = "#315477"      # Sidebar divider
COLOR_SIDEBAR_GRADIENT_END = "#0B2545" # Sidebar background
COLOR_LIGHT_BLUE = "#DBEAFE"           # Light blue
COLOR_PALE_BLUE = "#EFF6FF"            # Pale blue
COLOR_MAIN_BG = "#FFFFFF"              # Main background
COLOR_SECONDARY_BG = "#F8FAFC"         # Secondary background
COLOR_TEXT_PRIMARY = "#111827"         # Primary text
COLOR_TEXT_SECONDARY = "#475569"       # Secondary text
COLOR_BORDER = "#E2E8F0"               # Border
COLOR_SUCCESS = "#16A34A"              # Success
COLOR_SUCCESS_BG = "#DCFCE7"           # Success background
COLOR_WARNING = "#D97706"              # Warning
COLOR_ERROR = "#DC2626"                # Error

# Exact Sidebar Dimensions
SIDEBAR_EXPANDED_WIDTH = 320
SIDEBAR_COLLAPSED_WIDTH = 95
SIDEBAR_LOGO_SIZE = 60
SIDEBAR_ITEM_HEIGHT = 60
SIDEBAR_ICON_SIZE = 26
SIDEBAR_AVATAR_SIZE = 48

# Backward-compatible aliases for smooth transitions
COLOR_PRIMARY_DARK = COLOR_DARK_BLUE
COLOR_PRIMARY_LIGHT = COLOR_LIGHT_BLUE
COLOR_DARK_EMERALD = COLOR_DARK_BLUE       # Backward-compat alias
COLOR_DEEP_GREEN = COLOR_SIDEBAR_BG        # Backward-compat alias
COLOR_PALE_EMERALD = COLOR_LIGHT_BLUE      # Backward-compat alias
COLOR_LIGHT_GREEN_BG = COLOR_PALE_BLUE     # Backward-compat alias
COLOR_ACCENT = COLOR_PRIMARY
COLOR_BG_CARD = COLOR_MAIN_BG
COLOR_TEXT_MAIN = COLOR_TEXT_PRIMARY
COLOR_TEXT_MUTED = COLOR_TEXT_SECONDARY
COLOR_DANGER = COLOR_ERROR
COLOR_INFO = "#2563EB"

# Plotly theme colors aligned with the blue & white SaaS palette
PLOTLY_COLORWAY = [
    "#2563EB", "#1D4ED8", "#3B82F6", "#60A5FA", "#1E40AF",
    "#6366F1", "#8B5CF6", "#0D9488", "#D97706", "#EC4899"
]

# Supported file formats & upload limits
SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xls"]
MAX_FILE_SIZE_MB = 100

# Built-in default Groq API Key
DEFAULT_GROQ_API_KEY = ""


# Default Groq Models
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
FAST_GROQ_MODEL = "openai/gpt-oss-20b"
AVAILABLE_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

# Sample dataset directory
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")

