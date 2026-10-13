"""Google OAuth 2.0, OpenID Connect, and Guest authentication module for DataPilot AI."""
import os
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from datetime import datetime

import requests
import streamlit as st
from google.oauth2 import id_token
from google.auth.transport.requests import Request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Google OAuth 2.0 Endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_oauth_config() -> Dict[str, str]:
    """Retrieve Google OAuth configuration from Streamlit secrets or environment variables."""
    client_id = ""
    client_secret = ""
    redirect_uri = ""

    # 1. Try Streamlit secrets (support top-level and sections [google_oauth] & [google])
    try:
        if hasattr(st, "secrets"):
            client_id = st.secrets.get("GOOGLE_CLIENT_ID", "")
            client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI", "")

            # Check nested [google_oauth] section
            if not client_id and "google_oauth" in st.secrets:
                g_oauth = st.secrets["google_oauth"]
                client_id = g_oauth.get("client_id", "")
                client_secret = g_oauth.get("client_secret", "")
                redirect_uri = g_oauth.get("redirect_uri", "")

            # Check nested [google] section
            if not client_id and "google" in st.secrets:
                g_sec = st.secrets["google"]
                client_id = g_sec.get("client_id", "")
                client_secret = g_sec.get("client_secret", "")
                redirect_uri = g_sec.get("redirect_uri", "")
    except Exception as e:
        logger.debug(f"Could not read st.secrets: {e}")

    # 2. Fallback to environment variables
    if not client_id:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_secret:
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not redirect_uri:
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

    # Normalize redirect URI (strip trailing slash for exact Google Cloud matching)
    redirect_uri = redirect_uri.strip().rstrip("/") if redirect_uri else "http://localhost:8501"

    return {
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "redirect_uri": redirect_uri,
    }


def is_google_oauth_configured() -> bool:
    """Check if valid Google OAuth credentials have been configured."""
    config = get_oauth_config()
    client_id = config.get("client_id", "")
    client_secret = config.get("client_secret", "")

    # Reject placeholders
    placeholders = [
        "",
        "your_google_client_id_here",
        "your-client-id.apps.googleusercontent.com",
        "your_google_client_secret_here",
        "gocspx-your_google_client_secret",
    ]
    if client_id.lower() in placeholders or client_secret.lower() in placeholders:
        return False
    if "your_" in client_id.lower() or "your_" in client_secret.lower():
        return False
    return bool(len(client_id) > 12 and len(client_secret) > 6)


def get_google_auth_url() -> str:
    """Generate the Google OAuth 2.0 authorization URL with CSRF protection."""
    config = get_oauth_config()
    client_id = config["client_id"]
    redirect_uri = config["redirect_uri"]

    # Generate cryptographic CSRF state token
    state = secrets.token_urlsafe(32)
    st.session_state["oauth_state"] = state

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


def handle_oauth_callback() -> Optional[Dict[str, Any]]:
    """Inspect query parameters for Google OAuth callback, exchange token, and verify ID token."""
    if not hasattr(st, "query_params"):
        return None

    code = st.query_params.get("code")
    state = st.query_params.get("state")
    error = st.query_params.get("error")

    # Handle user cancellation or error from Google
    if error:
        st.session_state["auth_error"] = f"Google sign-in canceled or failed: {error}"
        st.query_params.clear()
        return None

    if not code:
        return None

    # Validate CSRF state if session state has persisted
    saved_state = st.session_state.get("oauth_state")
    if saved_state and state and state != saved_state:
        logger.warning("OAuth state token mismatch detected.")
        st.session_state["auth_error"] = "Security notice: OAuth state mismatch (possible CSRF attack)."
        st.query_params.clear()
        return None

    config = get_oauth_config()
    client_id = config["client_id"]
    client_secret = config["client_secret"]
    redirect_uri = config["redirect_uri"]

    if not client_id or not client_secret:
        st.session_state["auth_error"] = (
            "Google OAuth credentials are not configured on this server. "
            "Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
        st.query_params.clear()
        return None

    # Token exchange with Google
    try:
        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(GOOGLE_TOKEN_ENDPOINT, data=token_data, timeout=12)
        if resp.status_code != 200:
            err_msg = f"Token exchange failed with status {resp.status_code}"
            try:
                err_json = resp.json()
                if "error_description" in err_json:
                    err_msg = f"{err_json['error']}: {err_json['error_description']}"
                elif "error" in err_json:
                    err_msg = f"Error: {err_json['error']}"
            except Exception:
                err_msg = resp.text[:200]
            st.session_state["auth_error"] = f"Google authentication error: {err_msg}"
            st.query_params.clear()
            return None

        tokens = resp.json()
        raw_id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")

        if not raw_id_token:
            st.session_state["auth_error"] = "No OpenID Connect ID token returned by Google."
            st.query_params.clear()
            return None

        # Verify Google OpenID Connect ID token cryptographically
        claims = id_token.verify_oauth2_token(
            raw_id_token,
            Request(),
            audience=client_id
        )

        # Verify token issuer is Google
        issuer = claims.get("iss", "")
        if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
            st.session_state["auth_error"] = f"Untrusted token issuer: {issuer}"
            st.query_params.clear()
            return None

        # Fallback to UserInfo endpoint if picture or name missing
        user_name = claims.get("name")
        user_picture = claims.get("picture", "")
        user_email = claims.get("email")

        if access_token and (not user_name or not user_picture):
            try:
                u_resp = requests.get(
                    GOOGLE_USERINFO_ENDPOINT,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=5
                )
                if u_resp.status_code == 200:
                    u_data = u_resp.json()
                    user_name = user_name or u_data.get("name")
                    user_picture = user_picture or u_data.get("picture", "")
            except Exception as _e:
                logger.debug(f"UserInfo endpoint fallback failed: {_e}")

        user_info = {
            "id": claims.get("sub"),
            "email": user_email,
            "name": user_name or (user_email.split("@")[0].capitalize() if user_email else "Google User"),
            "picture": user_picture,
            "email_verified": claims.get("email_verified", False),
            "given_name": claims.get("given_name", ""),
            "family_name": claims.get("family_name", ""),
            "auth_provider": "google",
            "authenticated_at": datetime.now().isoformat(),
        }

        # Clear query params to clean URL
        st.query_params.clear()
        st.session_state["oauth_state"] = None
        st.session_state["auth_user"] = user_info
        st.session_state["auth_mode"] = "google"
        st.session_state["is_authenticated"] = True
        st.session_state.pop("auth_error", None)

        # Initialize user-specific isolated state
        initialize_user_session(user_info)
        st.rerun()
        return user_info

    except Exception as e:
        logger.exception("Error during Google OAuth callback processing")
        st.session_state["auth_error"] = f"Authentication verification failed: {str(e)}"
        st.query_params.clear()
        return None


# -------------------------------------------------------------
# Guest Authentication Functions
# -------------------------------------------------------------
def validate_guest_name(name: Optional[str]) -> Tuple[bool, str]:
    """Validate guest name input.
    
    Returns:
        (is_valid, cleaned_name_or_error_message)
    """
    if not name or not str(name).strip():
        return False, "Please enter your name."
    
    cleaned = str(name).strip()
    if len(cleaned) > 50:
        return False, "Name must be 50 characters or fewer."
    
    if len(cleaned) < 1:
        return False, "Name cannot be empty."
        
    return True, cleaned


def login_guest_user(name: str) -> Optional[Dict[str, Any]]:
    """Log in the user as a temporary guest with name only."""
    is_valid, result = validate_guest_name(name)
    if not is_valid:
        st.session_state["auth_error"] = result
        return None
    
    cleaned_name = result
    guest_user = {
        "id": f"guest_{secrets.token_hex(6)}",
        "email": None,
        "name": cleaned_name,
        "picture": None,
        "is_guest": True,
        "auth_provider": "guest",
        "authenticated_at": datetime.now().isoformat(),
    }
    
    st.session_state["auth_user"] = guest_user
    st.session_state["auth_mode"] = "guest"
    st.session_state["is_authenticated"] = True
    st.session_state.pop("auth_error", None)
    initialize_user_session(guest_user)
    return guest_user


def update_guest_name(new_name: str) -> bool:
    """Update the display name of the current guest session."""
    is_valid, result = validate_guest_name(new_name)
    if not is_valid:
        st.session_state["auth_error"] = result
        return False
    
    cleaned = result
    if st.session_state.get("auth_user") and st.session_state.get("auth_mode") == "guest":
        st.session_state["auth_user"]["name"] = cleaned
    return True


def initialize_user_session(user_info: Dict[str, Any]) -> None:
    """Ensure user session state is cleanly isolated for the authenticated user or guest."""
    user_id = user_info.get("id") or user_info.get("email") or user_info.get("name")
    prev_user_id = st.session_state.get("_active_user_id")

    # If switching users, reset leftover dataset and chat state to guarantee privacy
    if prev_user_id != user_id:
        st.session_state["_active_user_id"] = user_id
        st.session_state["df"] = None
        st.session_state["file_name"] = None
        st.session_state["messages"] = []
        st.session_state["recent_datasets"] = {}
        st.session_state["cleaning_history"] = None
        st.session_state["profile"] = None
        st.session_state["active_sheet"] = None
        st.session_state["excel_sheets"] = []


def sign_out() -> None:
    """Sign out the current user or guest, clear tokens, and purge session data."""
    st.session_state["auth_user"] = None
    st.session_state["auth_mode"] = None
    st.session_state["is_authenticated"] = False
    st.session_state["_active_user_id"] = None
    st.session_state.pop("auth_error", None)

    # Purge user-specific data to guarantee privacy
    st.session_state["df"] = None
    st.session_state["file_name"] = None
    st.session_state["messages"] = []
    st.session_state["recent_datasets"] = {}
    st.session_state["cleaning_history"] = None
    st.session_state["profile"] = None
    st.session_state["active_sheet"] = None
    st.session_state["excel_sheets"] = None

    if hasattr(st, "query_params"):
        st.query_params.clear()
    st.rerun()


def login_demo_user(email: str = "gowtham@example.com", name: str = "Gowtham A", photo_url: str = "") -> None:
    """Convenience helper for evaluation."""
    demo_user = {
        "id": "demo_user_12345",
        "email": email,
        "name": name,
        "picture": photo_url or "https://lh3.googleusercontent.com/a/default-user=s96-c",
        "email_verified": True,
        "given_name": name.split()[0] if name else "Gowtham",
        "family_name": name.split()[-1] if len(name.split()) > 1 else "A",
        "auth_provider": "google_sandbox",
        "authenticated_at": datetime.now().isoformat(),
    }
    st.session_state["auth_user"] = demo_user
    st.session_state["auth_mode"] = "google"
    st.session_state["is_authenticated"] = True
    st.session_state.pop("auth_error", None)
    initialize_user_session(demo_user)
    st.rerun()
