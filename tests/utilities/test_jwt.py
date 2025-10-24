#!/usr/bin/env python3
"""Test JWT system manually."""

from datetime import datetime, timedelta

import requests
from jose import jwt


def create_test_token():
    """Create a test JWT token manually."""
    # Get user data from database
    import subprocess
    result = subprocess.run([
        "docker", "exec", "brownie-metadata-postgres",
        "psql", "-U", "brownie-fastapi-server", "-d", "brownie_metadata",
        "-c", "SELECT id, email, org_id, organization_id, team_id, role FROM users WHERE email = 'test@example.com';"
    ], capture_output=True, text=True)

    print("Database query result:")
    print(result.stdout)

    # Parse the result to get user data
    lines = result.stdout.strip().split('\n')
    if len(lines) >= 3:
        data_line = lines[2]  # Skip header and separator
        parts = [p.strip() for p in data_line.split('|')]
        if len(parts) >= 6:
            user_id = parts[0].strip()
            email = parts[1].strip()
            org_id = parts[2].strip()
            organization_id = parts[3].strip()
            team_id = parts[4].strip()
            role = parts[5].strip()

            print(f"User ID: {user_id}")
            print(f"Email: {email}")
            print(f"Org ID: {org_id}")
            print(f"Organization ID: {organization_id}")
            print(f"Team ID: {team_id}")
            print(f"Role: {role}")

            # Create JWT token
            token_data = {
                "sub": user_id,
                "email": email,
                "org_id": org_id,
                "roles": [role.lower()],
                "exp": datetime.utcnow() + timedelta(hours=1)
            }

            # Use the same secret as the server
            secret = "CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS"
            token = jwt.encode(token_data, secret, algorithm="HS256")

            print("\nGenerated JWT token:")
            print(token)
            return token

    return None

def test_protected_endpoints(token):
    """Test protected endpoints with the token."""
    base_url = "http://localhost:8080"
    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== Testing Protected Endpoints ===")

    # Test 1: Get current user
    print("\n1. Testing /api/v1/auth/me...")
    try:
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Get user by ID
    user_id = "c5ee69a2-ab73-4f9d-be44-aa90b0b51d0a"
    print(f"\n2. Testing /api/v1/users/{user_id}...")
    try:
        response = requests.get(f"{base_url}/api/v1/users/{user_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: List users in organization
    org_id = "c9e8f1b4-a7c6-4864-bd67-4ca80a7deebc"
    print(f"\n3. Testing /api/v1/organizations/{org_id}/users...")
    try:
        response = requests.get(f"{base_url}/api/v1/organizations/{org_id}/users", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    print("Testing JWT System Manually")
    print("=" * 40)

    token = create_test_token()
    if token:
        test_protected_endpoints(token)
    else:
        print("Failed to create test token")
