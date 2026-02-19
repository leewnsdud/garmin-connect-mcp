"""Pre-authentication CLI script for Garmin Connect.

Run this script once to authenticate and save tokens:
    uv run python scripts/auth.py
"""

import getpass
import sys
from pathlib import Path

from garminconnect import Garmin


def main():
    print("=== Garmin Connect Authentication ===\n")

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    if not email or not password:
        print("Error: Email and password are required.")
        sys.exit(1)

    token_dir = Path.home() / ".garminconnect"
    token_dir.mkdir(mode=0o700, exist_ok=True)
    token_dir = str(token_dir)

    print("\nAuthenticating...")

    try:
        garmin = Garmin(
            email=email,
            password=password,
            prompt_mfa=lambda: input("\nMFA code: ").strip(),
        )
        garmin.login()
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)

    # Save tokens to disk
    try:
        garmin.garth.dump(token_dir)
        print(f"\nAuthentication successful!")
        print(f"Tokens saved to: {token_dir}")
        print(f"\nYou can now start the MCP server.")
    except Exception as e:
        print(f"\nAuthentication succeeded but failed to save tokens: {e}")

    # Show basic profile info to confirm
    try:
        name = garmin.get_full_name()
        print(f"Logged in as: {name}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
