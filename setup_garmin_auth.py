#!/usr/bin/env python3
"""
Garmin Connect authentication setup script
This script helps generate and manage Garmin Connect tokens using Garth
"""
import os
import sys
import garth
import getpass
from pathlib import Path
from dotenv import load_dotenv
import shutil
from typing import Tuple

# Optional imports used for SSL troubleshooting
try:
    import certifi  # Provided transitively via requests
except Exception:
    certifi = None  # type: ignore
try:
    from requests.exceptions import SSLError  # type: ignore
except Exception:
    SSLError = Exception  # Fallback type

def get_token_dir() -> Path:
    """Determine token storage directory (default to ~/.garminconnect).

    Honors environment overrides commonly used by python-garminconnect:
    - GARMINTOKENS
    - GARMINCONNECT_TOKEN_DIR (fallback alias)
    """
    load_dotenv()
    env_dir = os.getenv("GARMINTOKENS") or os.getenv("GARMINCONNECT_TOKEN_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return Path.home() / ".garminconnect"

def migrate_legacy_tokens_if_needed(dest_dir: Path) -> None:
    """Migrate legacy ~/.garth tokens into dest_dir if present and dest is empty.

    This helps users who previously used garth-only tokens.
    """
    legacy_dir = Path.home() / ".garth"
    try:
        if legacy_dir.exists() and legacy_dir.is_dir():
            if not dest_dir.exists() or not any(dest_dir.glob("*")):
                dest_dir.mkdir(parents=True, exist_ok=True)
                for f in legacy_dir.glob("*.json"):
                    shutil.copy2(f, dest_dir / f.name)
                print(f"🔀 Migrated legacy tokens from {legacy_dir} → {dest_dir}")
    except Exception as e:
        print(f"⚠️  Token migration skipped due to error: {e}")

def configure_oauth_consumer_from_env() -> None:
    """Configure garth OAuth consumer from environment if provided.

    Supports both GARTH_OAUTH_KEY/SECRET and GARMIN_OAUTH_CONSUMER_KEY/SECRET.
    """
    load_dotenv()
    key = os.getenv("GARTH_OAUTH_KEY") or os.getenv("GARMIN_OAUTH_CONSUMER_KEY")
    secret = os.getenv("GARTH_OAUTH_SECRET") or os.getenv("GARMIN_OAUTH_CONSUMER_SECRET")
    if key and secret:
        try:
            garth.sso.OAUTH_CONSUMER = {"key": key, "secret": secret}
            print("🔧 Using custom OAuth consumer from environment")
        except Exception as e:
            print(f"⚠️  Failed to set custom OAuth consumer: {e}")

def is_ssl_cert_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        isinstance(exc, SSLError)
        or "certificate verify failed" in msg
        or "ssl: certificate_verify_failed" in msg
        or "unable to get local issuer certificate" in msg
    )

def configure_certifi_env() -> Tuple[bool, str]:
    """Point SSL env variables to certifi CA bundle if available.

    Returns (configured, path_or_reason)
    """
    try:
        if certifi is None:
            return (False, "certifi module not available")
        ca_path = certifi.where()
        # Do not overwrite if user already configured
        os.environ.setdefault("SSL_CERT_FILE", ca_path)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_path)
        return (True, ca_path)
    except Exception as e:
        return (False, f"{e}")

def get_credentials():
    """Get Garmin Connect credentials from user input or environment variables"""
    
    # Load environment variables first
    load_dotenv()
    
    # Check if credentials exist in environment
    env_username = os.getenv("GARMIN_USERNAME")
    env_password = os.getenv("GARMIN_PASSWORD")
    
    if env_username and env_password:
        print(f"📋 Found existing credentials in .env file")
        use_existing = input(f"Use existing username '{env_username}'? (y/n): ").lower().strip()
        
        if use_existing in ['y', 'yes', '']:
            return env_username, env_password
        else:
            print("🔄 Getting new credentials...")
    
    # Get credentials from user input
    print("\n📝 Enter your Garmin Connect credentials:")
    
    while True:
        username = input("Email address: ").strip()
        if username and '@' in username:
            break
        print("❌ Please enter a valid email address")
    
    while True:
        password = getpass.getpass("Password: ")
        if password:
            break
        print("❌ Password cannot be empty")
    
    # Ask if user wants to save credentials
    save_creds = input("\n💾 Save credentials to .env file? (y/n): ").lower().strip()
    
    if save_creds in ['y', 'yes', '']:
        save_credentials_to_env(username, password)
    
    return username, password

def save_credentials_to_env(username, password):
    """Save credentials to .env file"""
    
    env_file = Path(".env")
    
    # Create .env from template if it doesn't exist
    if not env_file.exists():
        template_file = Path(".env.template")
        if template_file.exists():
            shutil.copy(template_file, env_file)
            print("📋 Created .env file from template")
        else:
            # Create basic .env file
            env_content = f"""# Garmin Connect credentials
GARMIN_USERNAME={username}
GARMIN_PASSWORD={password}

# Optional: Custom OAuth consumer settings (leave blank to use defaults)
GARMIN_OAUTH_CONSUMER_KEY=
GARMIN_OAUTH_CONSUMER_SECRET=

# Optional: Alternative variable names for OAuth consumer (garth-native)
GARTH_OAUTH_KEY=
GARTH_OAUTH_SECRET=

# Optional: Token storage directory override (default: ~/.garminconnect)
# Commonly used by python-garminconnect
GARMINTOKENS=
GARMINCONNECT_TOKEN_DIR=

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
            env_file.write_text(env_content)
            print("📋 Created new .env file")
    else:
        # Update existing .env file
        lines = []
        content = env_file.read_text()
        
        username_updated = False
        password_updated = False
        
        for line in content.split('\n'):
            if line.startswith('GARMIN_USERNAME='):
                lines.append(f'GARMIN_USERNAME={username}')
                username_updated = True
            elif line.startswith('GARMIN_PASSWORD='):
                lines.append(f'GARMIN_PASSWORD={password}')
                password_updated = True
            else:
                lines.append(line)
        
        # Add missing entries
        if not username_updated:
            lines.append(f'GARMIN_USERNAME={username}')
        if not password_updated:
            lines.append(f'GARMIN_PASSWORD={password}')
        
        env_file.write_text('\n'.join(lines))
        print("📋 Updated .env file with new credentials")

def remove_token_directories(dirs):
    for tdir in dirs:
        try:
            if tdir.exists():
                shutil.rmtree(tdir)
                print(f"🗑️  Removed tokens at {tdir}")
        except Exception as e:
            print(f"⚠️  Failed to remove {tdir}: {e}")

def setup_authentication(fresh: bool = False):
    """Setup Garmin Connect authentication tokens.

    If fresh=True or AUTH_FRESH/GARMINTOKENS_FRESH is set, existing tokens are deleted first.
    """
    
    print("🏃‍♂️ Garmin Connect MCP Server - Authentication Setup")
    print("=" * 60)
    
    # Fresh mode determination (CLI param or env)
    env_fresh = str(os.getenv("AUTH_FRESH", "")).lower() in ["1", "true", "yes", "y"] or \
                str(os.getenv("GARMINTOKENS_FRESH", "")).lower() in ["1", "true", "yes", "y"]

    # Configure optional OAuth consumer
    configure_oauth_consumer_from_env()

    # Setup token storage (prefer ~/.garminconnect or GARMINTOKENS)
    token_dir = get_token_dir()
    legacy_dir = Path.home() / ".garth"

    # Fresh cleanup before anything else
    if fresh or env_fresh:
        print("🧹 Fresh setup requested - removing existing token directories...")
        remove_token_directories([token_dir, legacy_dir])
    
    # Get credentials from user input or environment
    username, password = get_credentials()
    
    if not username or not password:
        print("❌ Valid credentials are required!")
        return False
    
    print(f"📧 Username: {username}")
    print("🔐 Password: [HIDDEN]")
    
    print(f"📁 Token storage: {token_dir}")

    # If not fresh, optionally migrate legacy tokens
    if not (fresh or env_fresh):
        migrate_legacy_tokens_if_needed(token_dir)
    
    # Check if tokens already exist
    if token_dir.exists() and list(token_dir.glob("*.json")):
        print("\n🔍 Existing tokens found. Testing...")
        # Ask user whether to reuse or delete when interactive
        try:
            choice = input("Reuse existing tokens? (Y/n, 'd' to delete and re-auth): ").strip().lower()
        except Exception:
            choice = ""
        if choice in ["n", "no", "d", "delete"]:
            print("🧹 Deleting existing tokens and continuing with fresh authentication...")
            remove_token_directories([token_dir, legacy_dir])
        else:
            try:
                garth.resume(str(token_dir))
                print("✅ Existing tokens are valid!")
                return test_api_access(token_dir)
            except Exception as e:
                print(f"⚠️  Existing tokens invalid: {e}")
                print("🔄 Proceeding with fresh authentication...")
    
    # Attempt authentication
    print(f"\n🔐 Attempting to authenticate with Garmin Connect...")
    
    try:
        # Method 1: Standard login
        print("Method 1: Standard authentication...")
        garth.login(username, password)
        print("✅ Authentication successful!")
        
        # Save tokens
        garth.save(str(token_dir))
        print(f"💾 Tokens saved to {token_dir}")
        
        return test_api_access(token_dir)
        
    except Exception as e:
        error_msg = str(e).lower()

        # SSL certificate issues: attempt auto-fix via certifi and retry once
        if is_ssl_cert_error(e):
            print("\n🚧 SSL 인증서 검증 오류를 감지했습니다. 자동으로 CA 번들을 설정해 재시도합니다.")
            ok, info = configure_certifi_env()
            if ok:
                print(f"🔒 Using CA bundle: {info}")
            else:
                print(f"⚠️  Unable to configure certifi CA bundle automatically: {info}")

            try:
                garth.login(username, password)
                garth.save(str(token_dir))
                print("✅ 재시도 성공: 인증 완료 및 토큰 저장")
                return test_api_access(token_dir)
            except Exception as retry_err:
                print(f"❌ 재시도 실패: {retry_err}")
                print("\n🔧 해결 가이드:")
                print("- macOS: Python.org 배포본 사용 시 'Install Certificates.command' 실행")
                print("- certifi 최신화: uv run python -m pip install -U certifi")
                print("- 환경변수로 CA 번들 지정: export SSL_CERT_FILE=$(python -c 'import certifi;print(certifi.where())'); export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE")
                print("- 사내 프록시/보안 솔루션 사용 시, 조직 루트 CA를 REQUESTS_CA_BUNDLE로 지정")
                print("- 네트워크/프록시 설정 확인 후 재시도")
                return False

        if "mfa" in error_msg or "verification" in error_msg:
            print("🔐 Multi-Factor Authentication (MFA) required!")
            return handle_mfa_login(username, password, token_dir)
        elif "401" in error_msg or "unauthorized" in error_msg:
            print("❌ Authentication failed: Invalid credentials or account locked")
            print("\n🔧 Troubleshooting steps:")
            print("1. Verify your credentials are correct")
            print("2. Check if 2FA is enabled (you may need to disable it temporarily)")
            print("3. Try logging into Garmin Connect website first")
            print("4. Check if your account is locked or has security restrictions")
            return False
        else:
            print(f"❌ Authentication failed: {e}")
            return False

def handle_mfa_login(username, password, token_dir):
    """Handle Multi-Factor Authentication login"""
    
    try:
        print("\n🔐 Attempting MFA authentication...")
        
        # Try advanced MFA handling
        result1, result2 = garth.login(username, password, return_on_mfa=True)
        
        if result1 == "needs_mfa":
            print("📱 MFA code required!")
            print("Please check your authenticator app or SMS for the verification code.")
            
            # Get MFA code from user
            while True:
                mfa_code = input("Enter MFA code (6 digits): ").strip()
                if mfa_code.isdigit() and len(mfa_code) == 6:
                    break
                print("❌ Please enter a valid 6-digit code")
            
            # Complete MFA login
            oauth1, oauth2 = garth.resume_login(result2, mfa_code)
            print("✅ MFA authentication successful!")
            
            # Save tokens
            garth.save(str(token_dir))
            print(f"💾 Tokens saved to {token_dir}")
            
            return test_api_access(token_dir)
        else:
            print("✅ Authentication successful without MFA!")
            garth.save(str(token_dir))
            return test_api_access(token_dir)
            
    except Exception as e:
        print(f"❌ MFA authentication failed: {e}")
        return False

def test_api_access(token_dir: Path):
    """Test if API access is working via both garth and python-garminconnect."""
    
    print("\n🧪 Testing API access...")
    
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test basic API call with garth
        try:
            steps = garth.DailySteps.get(today)
            if steps:
                step_count = getattr(steps, 'steps', 'N/A')
                print(f"✅ API access successful! Today's steps: {step_count}")
            else:
                print("✅ API access successful! (No step data for today)")
        except Exception as api_error:
            print(f"⚠️  API test failed: {api_error}")
            print("✅ But authentication tokens were created successfully")

        # Additional test with python-garminconnect if available
        try:
            from garminconnect import Garmin
            gc_user = os.getenv("GARMIN_USERNAME")
            gc_pass = os.getenv("GARMIN_PASSWORD")
            if gc_user and gc_pass:
                client = Garmin(gc_user, gc_pass)
                try:
                    # Prefer token login first
                    client.login(str(token_dir))
                    print("✅ garminconnect: token login successful")
                except Exception as token_login_err:
                    print(f"ℹ️  garminconnect: token login failed, trying credential login ({token_login_err})")
                    client.login()
                    print("✅ garminconnect: credential login successful")
                try:
                    stats = client.get_stats(today)
                    rhr = None
                    try:
                        hr = client.get_heart_rates(today) or {}
                        rhr = hr.get('restingHeartRate') if isinstance(hr, dict) else None
                    except Exception:
                        pass
                    print(f"✅ garminconnect API test OK (stats keys: {list(stats.keys())[:3]})" + (f", RHR: {rhr}" if rhr is not None else ""))
                except Exception as gc_api_err:
                    print(f"⚠️  garminconnect API test failed: {gc_api_err}")
        except ImportError:
            # garminconnect not installed, skip secondary test
            pass
        
        print("\n🎉 Setup complete!")
        print("You can now use the Garmin Connect MCP server.")
        print("\nNext steps:")
        print("1. Add the server to Claude: claude mcp add garmin-connect file:///path/to/main.py")
        print("2. Start using the running analysis tools!")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def check_token_status():
    """Check current token status"""
    
    print("🔍 Checking Garmin Connect token status...")
    print("=" * 50)
    
    token_dir = get_token_dir()
    
    if not token_dir.exists():
        print("❌ No tokens found. Run setup first.")
        return False
    
    try:
        garth.resume(str(token_dir))
        print("✅ Tokens are valid and ready to use!")
        return test_api_access(token_dir)
    except Exception as e:
        print(f"❌ Tokens are invalid: {e}")
        print("🔄 Please run setup again to re-authenticate")
        return False

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_token_status()
        elif sys.argv[1] == "reset":
            print("🔄 Resetting authentication...")
            print("=" * 40)
            
            # Remove tokens in both new and legacy locations
            token_dirs = [get_token_dir(), Path.home() / ".garth"]
            for tdir in token_dirs:
                if tdir.exists():
                    try:
                        shutil.rmtree(tdir)
                        print(f"🗑️  Removed tokens at {tdir}")
                    except Exception as e:
                        print(f"⚠️  Failed to remove {tdir}: {e}")
            
            # Run setup
            setup_authentication()
        elif sys.argv[1] in ["help", "-h", "--help"]:
            print("🏃‍♂️ Garmin Connect MCP Server - Authentication Setup")
            print("=" * 60)
            print("Usage:")
            print("  python setup_garmin_auth.py        # Interactive setup")
            print("  python setup_garmin_auth.py check  # Check token status")
            print("  python setup_garmin_auth.py reset  # Reset and re-authenticate")
            print("  python setup_garmin_auth.py help   # Show this help")
        else:
            print(f"❌ Unknown command: {sys.argv[1]}")
            print("Run 'python setup_garmin_auth.py help' for usage information")
    else:
        setup_authentication()

if __name__ == "__main__":
    main()