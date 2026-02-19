"""Authentication module for Garmin Connect."""

import os
from pathlib import Path

from garminconnect import Garmin


def get_token_dir() -> str:
    """Get the token storage directory path, creating it if needed."""
    token_dir = Path(os.environ.get("GARMIN_TOKEN_DIR", str(Path.home() / ".garminconnect")))
    token_dir.mkdir(mode=0o700, exist_ok=True)
    return str(token_dir)


def _has_saved_tokens() -> bool:
    """Check if token files exist on disk."""
    token_dir = Path(get_token_dir())
    return (token_dir / "oauth1_token.json").exists() and (token_dir / "oauth2_token.json").exists()


def load_token(garmin: Garmin) -> bool:
    """Try to load saved tokens. Returns True if successful."""
    # Try base64 encoded token from environment variable
    garmintokens = os.environ.get("GARMINTOKENS")
    if garmintokens:
        try:
            garmin.login(tokenstore=garmintokens)
            return True
        except Exception:
            pass

    # Try loading from token directory (only if token files exist)
    if _has_saved_tokens():
        try:
            garmin.login(tokenstore=get_token_dir())
            return True
        except Exception:
            pass

    return False


def login_with_credentials(garmin: Garmin) -> bool:
    """Try to login using environment variable credentials. Returns True if successful."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        return False

    try:
        garmin.login()
        # Save tokens for next time
        garmin.garth.dump(get_token_dir())
        return True
    except Exception:
        return False


def create_client() -> Garmin:
    """Create and authenticate a Garmin client.

    Authentication priority:
    1. Saved tokens (from token directory or GARMINTOKENS env var)
    2. Environment variable credentials (GARMIN_EMAIL/GARMIN_PASSWORD)

    Raises RuntimeError if authentication fails.
    """
    email = os.environ.get("GARMIN_EMAIL", "")
    password = os.environ.get("GARMIN_PASSWORD", "")

    garmin = Garmin(email=email or None, password=password or None)

    # Try saved tokens first
    if load_token(garmin):
        return garmin

    # Try credentials
    if login_with_credentials(garmin):
        return garmin

    raise RuntimeError(
        "Garmin authentication failed. Please run 'uv run python scripts/auth.py' "
        "to authenticate first, or set GARMIN_EMAIL and GARMIN_PASSWORD environment variables."
    )
