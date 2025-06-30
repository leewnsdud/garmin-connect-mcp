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
            import shutil
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

def setup_authentication():
    """Setup Garmin Connect authentication tokens"""
    
    print("🏃‍♂️ Garmin Connect MCP Server - Authentication Setup")
    print("=" * 60)
    
    # Get credentials from user input or environment
    username, password = get_credentials()
    
    if not username or not password:
        print("❌ Valid credentials are required!")
        return False
    
    print(f"📧 Username: {username}")
    print("🔐 Password: [HIDDEN]")
    
    # Setup token storage
    token_dir = Path.home() / ".garth"
    print(f"📁 Token storage: {token_dir}")
    
    # Check if tokens already exist
    if token_dir.exists() and list(token_dir.glob("*.json")):
        print("\n🔍 Existing tokens found. Testing...")
        try:
            garth.resume(str(token_dir))
            print("✅ Existing tokens are valid!")
            return test_api_access()
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
        
        return test_api_access()
        
    except Exception as e:
        error_msg = str(e).lower()
        
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
            
            return test_api_access()
        else:
            print("✅ Authentication successful without MFA!")
            garth.save(str(token_dir))
            return test_api_access()
            
    except Exception as e:
        print(f"❌ MFA authentication failed: {e}")
        return False

def test_api_access():
    """Test if API access is working"""
    
    print("\n🧪 Testing API access...")
    
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test basic API call
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
    
    token_dir = Path.home() / ".garth"
    
    if not token_dir.exists():
        print("❌ No tokens found. Run setup first.")
        return False
    
    try:
        garth.resume(str(token_dir))
        print("✅ Tokens are valid and ready to use!")
        return test_api_access()
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
            
            # Remove existing tokens
            token_dir = Path.home() / ".garth"
            if token_dir.exists():
                import shutil
                shutil.rmtree(token_dir)
                print("🗑️  Removed existing tokens")
            
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