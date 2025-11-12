#!/usr/bin/env python3
"""
Setup Verification Script
Checks that all components are configured correctly for ACA Lead Extraction
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check environment variables"""
    print("=" * 60)
    print("1. ENVIRONMENT VARIABLES")
    print("=" * 60)

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("[WW]  python-dotenv not installed, checking environment directly")

    required_vars = {
        'ANTHROPIC_API_KEY': 'Claude API access',
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase API key'
    }

    optional_vars = {
        'GOOGLE_DRIVE_FOLDER_ID': 'Google Drive uploads',
        'SLACK_WEBHOOK_URL': 'Slack notifications'
    }

    all_good = True

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the value for security
            if len(value) > 20:
                masked = value[:10] + "..." + value[-10:]
            else:
                masked = value[:5] + "..."
            print(f"[OK] {var}: {masked}")
        else:
            print(f"[!!] {var}: NOT SET ({description})")
            all_good = False

    print("\nOptional:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"[OK] {var}: configured ({description})")
        else:
            print(f"[  ] {var}: not set ({description})")

    return all_good

def check_files():
    """Check that required files exist"""
    print("\n" + "=" * 60)
    print("2. REQUIRED FILES")
    print("=" * 60)

    required_files = [
        'extract_all_deals-properly-mcp.py',
        'mcp_functions.py',
        'supabase_schema.sql',
        'requirements.txt',
        '.env'
    ]

    all_good = True

    for filename in required_files:
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"[OK] {filename} ({size:,} bytes)")
        else:
            print(f"[!!] {filename}: NOT FOUND")
            all_good = False

    return all_good

def check_python_packages():
    """Check that required Python packages are installed"""
    print("\n" + "=" * 60)
    print("3. PYTHON PACKAGES")
    print("=" * 60)

    required_packages = {
        'anthropic': 'Claude API client',
        'supabase': 'Supabase client',
        'tqdm': 'Progress bars',
        'dotenv': 'Environment variables'
    }

    optional_packages = {
        'googleapiclient': 'Google Drive API',
        'requests': 'HTTP requests (Slack)'
    }

    all_good = True

    for package, description in required_packages.items():
        try:
            if package == 'dotenv':
                import dotenv
                version = getattr(dotenv, '__version__', 'unknown')
            else:
                mod = __import__(package)
                version = getattr(mod, '__version__', 'unknown')
            print(f"[OK] {package}: {version} ({description})")
        except ImportError:
            print(f"[!!] {package}: NOT INSTALLED ({description})")
            all_good = False

    print("\nOptional:")
    for package, description in optional_packages.items():
        try:
            mod = __import__(package)
            version = getattr(mod, '__version__', 'unknown')
            print(f"[OK] {package}: {version} ({description})")
        except ImportError:
            print(f"[  ] {package}: not installed ({description})")

    return all_good

def check_supabase_connection():
    """Test Supabase connection"""
    print("\n" + "=" * 60)
    print("4. SUPABASE CONNECTION")
    print("=" * 60)

    try:
        from supabase import create_client

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            print("[!!] Supabase credentials not found in .env")
            return False

        print(f"[+] Connecting to: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)

        # Test connection by querying tables
        try:
            result = supabase.table('leads').select('count').limit(1).execute()
            print("[OK] Connection successful!")
            print("[OK] Tables exist and are accessible")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if 'does not exist' in error_msg or 'relation' in error_msg:
                print("[WW]  Connection works, but tables not created yet")
                print("[>] Action needed: Run supabase_schema.sql in Supabase SQL Editor")
                print("   URL: https://supabase.com/dashboard/project/delgvqjilrzjigdovxao/editor")
                return False
            else:
                print(f"[WW]  Connection issue: {e}")
                return False

    except ImportError:
        print("[!!] supabase package not installed")
        print("   Run: pip install supabase")
        return False
    except Exception as e:
        print(f"[!!] Connection failed: {e}")
        return False

def check_mcp_config():
    """Check MCP configuration"""
    print("\n" + "=" * 60)
    print("5. MCP CONFIGURATION")
    print("=" * 60)

    mcp_file = Path('.vscode/mcp.json')
    if mcp_file.exists():
        print(f"[OK] MCP config exists: {mcp_file}")
        try:
            import json
            with open(mcp_file) as f:
                config = json.load(f)
            if 'mcpServers' in config and 'supabase' in config['mcpServers']:
                print("[OK] Supabase MCP server configured")
                return True
            else:
                print("[WW]  MCP config exists but Supabase not configured")
                return False
        except Exception as e:
            print(f"[WW]  Could not parse MCP config: {e}")
            return False
    else:
        print("[  ] MCP config not found (optional)")
        return True

def main():
    """Run all checks"""
    print("\n" + "=" * 60)
    print("ACA LEAD EXTRACTION - SETUP VERIFICATION")
    print("=" * 60)
    print()

    results = {
        'Environment': check_environment(),
        'Files': check_files(),
        'Packages': check_python_packages(),
        'Supabase': check_supabase_connection(),
        'MCP': check_mcp_config()
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for check, passed in results.items():
        status = "[OK] PASS" if passed else "[!!] NEEDS ATTENTION"
        print(f"{check:15s}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("[*] ALL CHECKS PASSED!")
        print("\nYour system is ready to extract leads.")
        print("\nNext steps:")
        print("1. Configure Gmail MCP server (see MCP_SETUP_GUIDE.md)")
        print("2. Test extraction: python extract_all_deals-properly-mcp.py --max 5")
    else:
        print("[WW]  SOME CHECKS FAILED")
        print("\nPlease review the issues above and:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Create database tables: Run supabase_schema.sql in Supabase")
        print("3. Check .env file has all required variables")
        print("\nSee SETUP_INSTRUCTIONS.md for detailed help")

    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
