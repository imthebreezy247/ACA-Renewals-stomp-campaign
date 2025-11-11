#!/usr/bin/env python3
"""
SETUP VERIFICATION SCRIPT
Run this FIRST to check if everything is configured correctly
"""

import sys
import os

def check_python_version():
    """Check if Python version is 3.7+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print("✅ Python version OK:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("❌ Python version too old:", f"{version.major}.{version.minor}")
        print("   Need Python 3.7 or higher")
        print("   Download from: https://www.python.org/downloads/")
        return False

def check_packages():
    """Check if required packages are installed"""
    required = [
        'google.auth',
        'google.oauth2',
        'googleapiclient',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ Package '{package}' installed")
        except ImportError:
            print(f"❌ Package '{package}' NOT installed")
            missing.append(package)
    
    if missing:
        print("\n📦 To install missing packages, run:")
        print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    
    return True

def check_credentials():
    """Check if credentials.json exists"""
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        return True
    else:
        print("❌ credentials.json NOT found")
        print("\n📋 To get credentials.json:")
        print("   1. Go to: https://console.cloud.google.com")
        print("   2. Create project and enable Gmail API")
        print("   3. Create OAuth credentials (Desktop app)")
        print("   4. Download as credentials.json")
        print("   5. Place in this directory")
        return False

def check_script():
    """Check if main script exists"""
    if os.path.exists('extract_all_daniel_hera_deals.py'):
        print("✅ Main extraction script found")
        return True
    else:
        print("❌ Main script NOT found")
        print("   Looking for: extract_all_daniel_hera_deals.py")
        return False

def main():
    print("=" * 60)
    print("  GMAIL EXTRACTOR - SETUP VERIFICATION")
    print("=" * 60)
    print("\nChecking your setup...\n")
    
    checks = [
        ("Python Version", check_python_version()),
        ("Required Packages", check_packages()),
        ("Credentials File", check_credentials()),
        ("Extraction Script", check_script()),
    ]
    
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    
    all_passed = all(result for _, result in checks)
    
    if all_passed:
        print("\n✅ ✅ ✅ ALL CHECKS PASSED! ✅ ✅ ✅")
        print("\nYou're ready to run the extraction script!")
        print("\nNext step:")
        print("   python extract_all_daniel_hera_deals.py")
        print("\nor on Mac/Linux:")
        print("   python3 extract_all_daniel_hera_deals.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\nRefer to SETUP_GUIDE.md for detailed instructions.")
        
        failed = [name for name, result in checks if not result]
        print(f"\nFailed checks: {', '.join(failed)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
