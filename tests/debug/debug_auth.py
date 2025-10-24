#!/usr/bin/env python3
"""Debug authentication issues."""


import requests


def test_auth_debug():
    """Test authentication with detailed debugging."""
    base_url = "http://localhost:8080"

    print("=== Testing Authentication Debug ===")

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Login with detailed error info
    print("\n2. Testing login endpoint...")
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Check if user exists in database
    print("\n3. Checking user in database...")
    import subprocess
    try:
        result = subprocess.run([
            "docker", "exec", "brownie-metadata-postgres",
            "psql", "-U", "brownie-fastapi-server", "-d", "brownie_metadata",
            "-c", "SELECT id, email, username, is_active, password_hash FROM users WHERE email = 'test@example.com';"
        ], capture_output=True, text=True)
        print("   Database query result:")
        print(f"   {result.stdout}")
        if result.stderr:
            print(f"   Error: {result.stderr}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_auth_debug()
