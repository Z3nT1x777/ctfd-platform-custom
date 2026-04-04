#!/usr/bin/env python3
"""
Generate or retrieve CTFd API token for admin user.
Useful for automating challenge sync operations.
"""

import sys
import json
import requests
from pathlib import Path

def get_or_create_token(ctfd_url: str, admin_user: str = "admin", admin_pass: str = "") -> str:
    """
    Login to CTFd and get/create an API token.
    
    Args:
        ctfd_url: Base CTFd URL (e.g., http://192.168.56.10)
        admin_user: Admin username 
        admin_pass: Admin password (if empty, tries to create user first)
        
    Returns:
        API token string
    """
    session = requests.Session()
    base_url = ctfd_url.rstrip('/')
    
    # Try login
    login_page = session.get(f"{base_url}/login")
    csrf_token = extract_csrf_from_html(login_page.text)
    
    if not csrf_token:
        print("❌ Could not find CSRF token, CTFd setup might be needed")
        sys.exit(1)
    
    login_data = {
        "name": admin_user,
        "password": admin_pass or "admin",
        "nonce": csrf_token,
    }
    
    login_resp = session.post(
        f"{base_url}/login",
        data=login_data,
        allow_redirects=True
    )
    
    # Check if logged in
    if login_resp.status_code != 200 or "challenges" not in login_resp.url:
        print(f"❌ Login failed for user '{admin_user}'")
        print(f"   Response: {login_resp.status_code}, URL: {login_resp.url}")
        sys.exit(1)
    
    print(f"✅ Logged in as '{admin_user}'")
    
    # Get settings page to fetch existing tokens
    settings = session.get(f"{base_url}/settings")
    
    # Extract CSRF for token creation
    csrf_token = extract_csrf_from_html(settings.text)
    
    if not csrf_token:
        print("❌ Could not find CSRF token on settings page")
        sys.exit(1)
    
    # Create new API token
    token_resp = session.post(
        f"{base_url}/api/v1/tokens",
        json={"nonce": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    
    if token_resp.status_code == 200:
        token_data = token_resp.json()
        if "data" in token_data and "value" in token_data["data"]:
            token = token_data["data"]["value"]
            print(f"✅ Generated new API token: {token}")
            return token
    
    print(f"❌ Failed to generate token: {token_resp.status_code}")
    print(f"   Response: {token_resp.text}")
    sys.exit(1)

def extract_csrf_from_html(html: str) -> str:
    """Extract CSRF token from HTML."""
    import re
    match = re.search(r'csrfNonce["\']?:\s*["\']([a-f0-9]+)["\']', html)
    if match:
        return match.group(1)
    return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_ctfd_admin_token.py <ctfd_url> [username] [password]")
        print("Example: python get_ctfd_admin_token.py http://192.168.56.10")
        sys.exit(1)
    
    ctfd_url = sys.argv[1]
    admin_user = sys.argv[2] if len(sys.argv) > 2 else "admin"
    admin_pass = sys.argv[3] if len(sys.argv) > 3 else ""
    
    token = get_or_create_token(ctfd_url, admin_user, admin_pass)
    print(f"\n📋 Use this token:\n{token}\n")
    print(f"💡 Or export as env var: export CTFD_API_TOKEN={token}")
