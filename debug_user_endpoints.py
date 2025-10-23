#!/usr/bin/env python3
"""Debug user endpoints to find the specific error."""

import requests
import json
import traceback

BASE_URL = "http://localhost:8080"

def debug_user_endpoints():
    """Debug the failing user endpoints."""
    print("=== Debugging User Endpoints ===")
    
    # Get token
    print("1. Getting authentication token...")
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    
    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Token obtained: {token[:50]}...")
    
    # Test user endpoints
    user_id = "c5ee69a2-ab73-4f9d-be44-aa90b0b51d0a"
    org_id = "c9e8f1b4-a7c6-4864-bd67-4ca80a7deebc"
    
    print(f"\n2. Testing GET /api/v1/users/{user_id}...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/{user_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 500:
            print("   ❌ 500 Internal Server Error")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
    
    print(f"\n3. Testing GET /api/v1/organizations/{org_id}/users...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/organizations/{org_id}/users", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 500:
            print("   ❌ 500 Internal Server Error")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_user_endpoints()
