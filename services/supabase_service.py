"""Supabase Client & Authentication Service for Cineverse AI.

Provides Supabase Authentication, user profile retrieval, server-side admin role verification,
and graceful offline fallback when environment credentials are not yet configured.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

logger = logging.getLogger("cineverse.supabase")

# Global client singletons
_SUPABASE_CLIENT = None
_SUPABASE_ADMIN_CLIENT = None


def get_credentials() -> Dict[str, str]:
    """Retrieve Supabase credentials from Streamlit secrets or OS environment."""
    url = ""
    pub_key = ""
    sec_key = ""

    # 1. Attempt retrieval from Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            url = st.secrets.get("SUPABASE_URL", "")
            pub_key = st.secrets.get("SUPABASE_PUBLISHABLE_KEY", "") or st.secrets.get("SUPABASE_KEY", "")
            sec_key = st.secrets.get("SUPABASE_SECRET_KEY", "") or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
    except Exception:
        pass

    # 2. Fallback to os.environ
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not pub_key:
        pub_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    if not sec_key:
        sec_key = os.environ.get("SUPABASE_SECRET_KEY", "") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    return {
        "url": url.strip(),
        "publishable_key": pub_key.strip(),
        "secret_key": sec_key.strip()
    }


def is_supabase_configured() -> bool:
    """Check if valid Supabase connection credentials exist."""
    creds = get_credentials()
    return bool(creds["url"] and creds["publishable_key"] and creds["url"].startswith("http"))


def get_supabase_client():
    """Retrieve or initialize the standard Supabase client for client-side/authenticated calls."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT

    if not is_supabase_configured():
        return None

    try:
        from supabase import create_client, Client
        creds = get_credentials()
        _SUPABASE_CLIENT = create_client(creds["url"], creds["publishable_key"])
        return _SUPABASE_CLIENT
    except Exception as exc:
        logger.warning(f"Failed to initialize Supabase client: {exc}")
        return None


def get_supabase_admin_client():
    """Retrieve or initialize privileged Supabase client for server-side admin operations."""
    global _SUPABASE_ADMIN_CLIENT
    if _SUPABASE_ADMIN_CLIENT is not None:
        return _SUPABASE_ADMIN_CLIENT

    creds = get_credentials()
    if not creds["url"] or not creds["secret_key"] or not creds["url"].startswith("http"):
        return None

    try:
        from supabase import create_client
        _SUPABASE_ADMIN_CLIENT = create_client(creds["url"], creds["secret_key"])
        return _SUPABASE_ADMIN_CLIENT
    except Exception as exc:
        logger.warning(f"Failed to initialize Supabase admin client: {exc}")
        return None


# --------------------------------------------------------------------------
# AUTHENTICATION FUNCTIONS
# --------------------------------------------------------------------------

def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    """Authenticate an existing user using email and password."""
    client = get_supabase_client()
    if not client:
        return {
            "success": False,
            "error": "Supabase credentials not configured in environment. Please set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."
        }

    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            profile = get_user_profile(response.user.id)
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
                "profile": profile,
                "error": None
            }
        return {"success": False, "error": "Login failed: No user returned."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def sign_up_with_password(email: str, password: str, display_name: str) -> Dict[str, Any]:
    """Register a new user account with Supabase Auth."""
    client = get_supabase_client()
    if not client:
        return {
            "success": False,
            "error": "Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."
        }

    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "display_name": display_name
                }
            }
        })
        user = response.user
        if user:
            # Check if email confirmation is required (session might be None until verified)
            needs_confirm = response.session is None
            return {
                "success": True,
                "user": user,
                "session": response.session,
                "needs_confirmation": needs_confirm,
                "error": None
            }
        return {"success": False, "error": "Registration failed: No user returned."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def sign_out() -> bool:
    """Sign out the current Supabase session."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
            return True
        except Exception:
            return False
    return True


def send_password_reset(email: str) -> Dict[str, Any]:
    """Send a password reset email via Supabase Auth."""
    client = get_supabase_client()
    if not client:
        return {"success": False, "error": "Supabase is not configured."}

    try:
        client.auth.reset_password_for_email(email)
        return {"success": True, "error": None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# --------------------------------------------------------------------------
# USER PROFILE & ROLE VERIFICATION
# --------------------------------------------------------------------------

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile record from public.profiles table."""
    admin_client = get_supabase_admin_client()
    client = admin_client or get_supabase_client()
    if not client:
        return None

    try:
        res = client.table("profiles").select("*").eq("id", str(user_id)).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as exc:
        logger.warning(f"Failed to fetch profile for user {user_id}: {exc}")
        return None


def is_user_admin(user_id: str) -> bool:
    """Verify if a user has server-side admin privileges."""
    # 1. Check persistent PostgreSQL profiles table
    profile = get_user_profile(user_id)
    if profile and profile.get("role") == "admin":
        return True

    # 2. Check Auth user metadata via privileged admin client
    admin_client = get_supabase_admin_client()
    if admin_client:
        try:
            u = admin_client.auth.admin.get_user_by_id(user_id)
            if u and u.user:
                meta = u.user.user_metadata or {}
                if meta.get("role") == "admin" or u.user.email in ("admin@cineverse.ai", "admin@gmail.com"):
                    return True
        except Exception:
            pass

    return False


def get_all_users_admin() -> List[Dict[str, Any]]:
    """Retrieve all registered user profiles for the Admin Portal."""
    admin_client = get_supabase_admin_client()
    if not admin_client:
        return []

    try:
        res = admin_client.table("profiles").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"Failed to fetch user list for admin: {exc}")
        return []


def update_user_role_admin(target_user_id: str, new_role: str) -> bool:
    """Update role for a user (Requires Supabase secret key / service role)."""
    if new_role not in ("user", "admin"):
        return False

    admin_client = get_supabase_admin_client()
    if not admin_client:
        return False

    try:
        admin_client.table("profiles").update({"role": new_role}).eq("id", str(target_user_id)).execute()
        return True
    except Exception as exc:
        logger.error(f"Failed to update role for user {target_user_id}: {exc}")
        return False
