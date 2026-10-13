"""Test suite for DataPilot AI Google OAuth 2.0 authentication and session management."""
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st

from src.auth.google_auth import (
    get_oauth_config,
    is_google_oauth_configured,
    get_google_auth_url,
    handle_oauth_callback,
    sign_out,
    login_demo_user,
    initialize_user_session,
)


def test_is_google_oauth_configured_default_false():
    """Verify that unconfigured environment returns False for OAuth configuration."""
    with patch.dict("os.environ", {}, clear=True):
        assert not is_google_oauth_configured()


def test_is_google_oauth_configured_valid_keys():
    """Verify that valid Google client credentials return True."""
    mock_env = {
        "GOOGLE_CLIENT_ID": "123456789-abcdef.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "GOCSPX-mock_secret_key_12345",
        "GOOGLE_REDIRECT_URI": "http://localhost:8501",
    }
    with patch.dict("os.environ", mock_env, clear=True):
        assert is_google_oauth_configured()
        config = get_oauth_config()
        assert config["client_id"] == mock_env["GOOGLE_CLIENT_ID"]
        assert config["client_secret"] == mock_env["GOOGLE_CLIENT_SECRET"]
        assert config["redirect_uri"] == "http://localhost:8501"


def test_get_google_auth_url_contains_params():
    """Verify authorization URL structure and CSRF state token generation."""
    mock_env = {
        "GOOGLE_CLIENT_ID": "123456789-abcdef.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "GOCSPX-mock_secret",
        "GOOGLE_REDIRECT_URI": "http://localhost:8501",
    }
    with patch.dict("os.environ", mock_env, clear=True):
        auth_url = get_google_auth_url()
        assert "accounts.google.com/o/oauth2/v2/auth" in auth_url
        assert "123456789-abcdef.apps.googleusercontent.com" in auth_url
        assert "scope=openid+email+profile" in auth_url or "scope=openid%20email%20profile" in auth_url
        assert "state=" in auth_url
        assert "oauth_state" in st.session_state
        assert len(st.session_state["oauth_state"]) > 20


def test_handle_oauth_callback_error_param():
    """Verify that OAuth callback errors from Google are handled gracefully."""
    st.query_params["error"] = "access_denied"
    user = handle_oauth_callback()
    assert user is None
    assert "access_denied" in st.session_state.get("auth_error", "")


def test_handle_oauth_callback_state_mismatch():
    """Verify CSRF defense rejects mismatched state."""
    st.session_state["oauth_state"] = "legitimate_state_12345"
    st.query_params["code"] = "mock_auth_code"
    st.query_params["state"] = "attacker_state_67890"

    user = handle_oauth_callback()
    assert user is None
    assert "CSRF" in st.session_state.get("auth_error", "") or "mismatch" in st.session_state.get("auth_error", "")


def test_login_demo_user_creates_profile():
    """Verify demo user authentication establishes session and verified profile."""
    with patch("streamlit.rerun"):
        login_demo_user(email="gowtham@example.com", name="Gowtham A")
        assert st.session_state.get("is_authenticated") is True
        user = st.session_state.get("auth_user")
        assert user is not None
        assert user["email"] == "gowtham@example.com"
        assert user["name"] == "Gowtham A"
        assert user["email_verified"] is True
        assert user["auth_provider"] == "google_sandbox"


def test_user_session_isolation():
    """Verify that switching accounts isolates session datasets and chat history."""
    st.session_state["_active_user_id"] = "user_alpha"
    st.session_state["df"] = MagicMock()
    st.session_state["file_name"] = "confidential_alpha.csv"
    st.session_state["messages"] = [{"role": "user", "content": "Alpha secret data"}]

    new_user = {"id": "user_beta", "email": "beta@example.com"}
    initialize_user_session(new_user)

    assert st.session_state["df"] is None
    assert st.session_state["file_name"] is None
    assert st.session_state["messages"] == []
    assert st.session_state["_active_user_id"] == "user_beta"


def test_sign_out_clears_all_user_data():
    """Verify that sign_out completely purges user state and datasets."""
    st.session_state["auth_user"] = {"email": "test@example.com", "name": "Test User"}
    st.session_state["is_authenticated"] = True
    st.session_state["df"] = MagicMock()
    st.session_state["file_name"] = "dataset.csv"
    st.session_state["messages"] = [{"role": "assistant", "content": "Data response"}]

    with patch("streamlit.rerun"):
        sign_out()
        assert st.session_state.get("auth_user") is None
        assert st.session_state.get("auth_mode") is None
        assert st.session_state.get("is_authenticated") is False
        assert st.session_state.get("df") is None
        assert st.session_state.get("file_name") is None
        assert st.session_state.get("messages") == []


def test_validate_guest_name():
    """Verify name validation rules for Guest login."""
    from src.auth.google_auth import validate_guest_name

    # Empty and whitespace
    is_valid, msg = validate_guest_name("")
    assert not is_valid
    assert "enter your name" in msg.lower() or "empty" in msg.lower()

    is_valid, msg = validate_guest_name("   ")
    assert not is_valid

    is_valid, msg = validate_guest_name(None)
    assert not is_valid

    # Overly long name (> 50 chars)
    is_valid, msg = validate_guest_name("A" * 51)
    assert not is_valid
    assert "50 characters" in msg.lower()

    # Valid names with whitespace trimming
    is_valid, cleaned = validate_guest_name("  Alex Morgan  ")
    assert is_valid
    assert cleaned == "Alex Morgan"

    is_valid, cleaned = validate_guest_name("Gowtham")
    assert is_valid
    assert cleaned == "Gowtham"


def test_login_guest_user():
    """Verify guest login initializes guest session state without requiring email or password."""
    from src.auth.google_auth import login_guest_user

    with patch("streamlit.rerun"):
        guest = login_guest_user("  Taylor Swift  ")
        assert guest is not None
        assert guest["name"] == "Taylor Swift"
        assert guest["is_guest"] is True
        assert guest["auth_provider"] == "guest"
        assert guest["email"] is None
        assert st.session_state.get("auth_mode") == "guest"
        assert st.session_state.get("is_authenticated") is True
        assert st.session_state.get("auth_user")["name"] == "Taylor Swift"


def test_update_guest_name():
    """Verify updating guest name updates session state."""
    from src.auth.google_auth import login_guest_user, update_guest_name

    with patch("streamlit.rerun"):
        login_guest_user("Initial Name")
        assert st.session_state["auth_user"]["name"] == "Initial Name"

        # Update with valid name
        success = update_guest_name("Updated Name")
        assert success is True
        assert st.session_state["auth_user"]["name"] == "Updated Name"

        # Update with invalid name fails
        fail = update_guest_name("   ")
        assert fail is False
        assert st.session_state["auth_user"]["name"] == "Updated Name"

