#!/usr/bin/env python3
"""Test script for user CRUD operations."""

import sys

import requests

BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

def test_user_endpoints():
    """Test user endpoints."""
    print("\nTesting user endpoints...")

    # Test getting user by ID (this will fail without auth, but let's see the error)
    user_id = "c5ee69a2-ab73-4f9d-be44-aa90b0b51d0a"  # From our database
    try:
        response = requests.get(f"{BASE_URL}/api/v1/users/{user_id}")
        print(f"Get user status: {response.status_code}")
        print(f"Get user response: {response.text}")
    except Exception as e:
        print(f"Get user failed: {e}")

    # Test listing users in organization
    org_id = "c9e8f1b4-a7c6-4864-bd67-4ca80a7deebc"  # From our database
    try:
        response = requests.get(f"{BASE_URL}/api/v1/organizations/{org_id}/users")
        print(f"List users status: {response.status_code}")
        print(f"List users response: {response.text}")
    except Exception as e:
        print(f"List users failed: {e}")

def test_auth_endpoints():
    """Test authentication endpoints."""
    print("\nTesting auth endpoints...")

    # Test login
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        print(f"Login status: {response.status_code}")
        print(f"Login response: {response.text}")
    except Exception as e:
        print(f"Login failed: {e}")

    # Test signup
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "username": "newuser",
            "full_name": "New User",
            "organization_name": "New Organization",
            "team_name": "New Team"
        })
        print(f"Signup status: {response.status_code}")
        print(f"Signup response: {response.text}")
    except Exception as e:
        print(f"Signup failed: {e}")

if __name__ == "__main__":
    print("Testing FastAPI User CRUD Endpoints")
    print("=" * 40)

    if not test_health():
        print("Server is not healthy, exiting...")
        sys.exit(1)

    test_auth_endpoints()
    test_user_endpoints()

    print("\nTest completed!")
