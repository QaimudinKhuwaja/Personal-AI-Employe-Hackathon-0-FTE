"""
Facebook Token Exchange Script

Exchanges a short-lived Facebook access token for a long-lived token.

Usage:
    python scripts/facebook_exchange_token.py
"""

import os
import sys
import requests
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def exchange_token():
    """Exchange short-lived token for long-lived token."""
    
    # Get credentials from env
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    short_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    
    print("=" * 60)
    print("FACEBOOK TOKEN EXCHANGE")
    print("=" * 60)
    
    if not all([app_id, app_secret, short_token]):
        print("\n[ERROR] Missing credentials in .env file!")
        print(f"  - FACEBOOK_APP_ID: {'Set' if app_id else 'MISSING'}")
        print(f"  - FACEBOOK_APP_SECRET: {'Set' if app_secret else 'MISSING'}")
        print(f"  - FACEBOOK_ACCESS_TOKEN: {'Set' if short_token else 'MISSING'}")
        return None
    
    print(f"\n[INFO] Using App ID: {app_id}")
    print(f"[INFO] Using App Secret: {app_secret[:20]}...")
    print(f"[INFO] Current token: {short_token[:30]}...")
    
    # Exchange token
    print("\n[INFO] Exchanging for long-lived token...")
    
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_token
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        result = response.json()
        
        if 'error' in result:
            error = result['error']
            print(f"\n[ERROR] Token exchange failed:")
            print(f"  - Type: {error.get('type', 'N/A')}")
            print(f"  - Message: {error.get('message', 'N/A')}")
            print(f"  - Code: {error.get('code', 'N/A')}")
            
            # Check if it's an expired token error
            if error.get('code') == 190:
                print("\n[WARN] Your current token is expired.")
                print("[INFO] You need to get a fresh short-lived token first:")
                print("   1. Go to: https://developers.facebook.com/tools/explorer/")
                print(f"   2. Select app: {app_id}")
                print("   3. Click 'Get Token' -> 'Get Page Access Token'")
                print("   4. Select your page and grant permissions")
                print("   5. Copy the new token and update .env file")
                print("   6. Run this script again to exchange for long-lived token")
            return None
        
        long_token = result.get('access_token')
        expires_in = result.get('expires_in', 5184000)  # Default 60 days
        
        print("\n" + "=" * 60)
        print("SUCCESS! Long-lived token obtained")
        print("=" * 60)
        print(f"\n[OK] New token: {long_token[:50]}...")
        print(f"[OK] Expires in: {expires_in} seconds ({expires_in // 86400} days)")
        
        # Get page token now
        print("\n[INFO] Getting Page access token...")
        
        # First get user ID from token debug
        debug_url = "https://graph.facebook.com/debug_token"
        debug_params = {
            'input_token': long_token,
            'access_token': f"{app_id}|{app_secret}"
        }
        
        debug_response = requests.get(debug_url, params=debug_params, timeout=10)
        debug_result = debug_response.json()
        
        user_id = debug_result.get('data', {}).get('user_id')
        
        if user_id:
            # Get page token
            page_url = f"https://graph.facebook.com/v18.0/{user_id}/accounts"
            page_params = {
                'access_token': long_token
            }
            
            page_response = requests.get(page_url, params=page_params, timeout=10)
            page_result = page_response.json()
            
            if 'data' in page_result and len(page_result['data']) > 0:
                for page in page_result['data']:
                    if page.get('id') == os.getenv('FACEBOOK_PAGE_ID'):
                        page_token = page.get('access_token')
                        print(f"\n[OK] Page access token: {page_token[:50]}...")
                        print(f"[OK] Page ID: {page.get('id')}")
                        print(f"[OK] Page Name: {page.get('name')}")
                        
                        print("\n" + "=" * 60)
                        print("UPDATE YOUR .ENV FILE")
                        print("=" * 60)
                        print(f"""
Replace this line in .env:
FACEBOOK_ACCESS_TOKEN={short_token[:50]}...

With this:
FACEBOOK_ACCESS_TOKEN={page_token}

This is a long-lived Page token that will last ~60 days!
""")
                        
                        return page_token
        
        # If no page token, return the user token
        print("\n" + "=" * 60)
        print("UPDATE YOUR .ENV FILE")
        print("=" * 60)
        print(f"""
Replace this line in .env:
FACEBOOK_ACCESS_TOKEN={short_token[:50]}...

With this:
FACEBOOK_ACCESS_TOKEN={long_token}

This is a long-lived user token that will last ~60 days!
""")
        
        return long_token
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


if __name__ == '__main__':
    token = exchange_token()
    
    if token:
        print("\n[SUCCESS] Token exchange complete!")
        print("[INFO] Remember to update your .env file with the new token")
        sys.exit(0)
    else:
        print("\n[ERROR] Token exchange failed!")
        sys.exit(1)
