"""Pre-authentication CLI script for Garmin Connect.

Run this script once to authenticate and save tokens:
    uv run python scripts/auth.py
"""

import getpass
import sys
from pathlib import Path

from garminconnect import Garmin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from garmin_mcp.auth import get_token_dir  # noqa: E402


def main():
    print("=== Garmin Connect Authentication ===\n")

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    if not email or not password:
        print("Error: Email and password are required.")
        sys.exit(1)

    # Same location the MCP server reads (GARMIN_TOKEN_DIR, default ~/.garminconnect).
    token_dir = get_token_dir()

    print("\nAuthenticating...")

    try:
        garmin = Garmin(
            email=email,
            password=password,
            prompt_mfa=lambda: input("\nMFA code: ").strip(),
        )
        # With a tokenstore path, login() also saves the tokens there.
        garmin.login(token_dir)
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)

    print(f"\nAuthentication successful!")
    print(f"Tokens saved to: {token_dir}")
    print(f"\nYou can now start the MCP server.")

    # Show basic profile info to confirm
    try:
        name = garmin.get_full_name()
        print(f"Logged in as: {name}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
