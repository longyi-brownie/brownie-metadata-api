"""Test authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_signup_success(client: TestClient, test_user_data):
    """Test successful user signup."""
    response = client.post("/api/v1/auth/signup", json=test_user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_signup_duplicate_email(client: TestClient, test_user_data):
    """Test signup with duplicate email fails."""
    # First signup
    client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Second signup with same email
    response = client.post("/api/v1/auth/signup", json=test_user_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient, test_user_data):
    """Test successful login."""
    # First signup
    client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Then login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_invalid_credentials(client: TestClient, test_user_data):
    """Test login with invalid credentials fails."""
    # First signup
    client.post("/api/v1/auth/signup", json=test_user_data)
    
    # Login with wrong password
    login_data = {
        "email": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with nonexistent user fails."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "password123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user_info(client: TestClient, test_user_data):
    """Test getting current user information."""
    # Signup and get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    
    # Get user info
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert data["full_name"] == test_user_data["full_name"]
    assert data["role"] == "admin"  # First user is admin
    assert "org_id" in data
    assert "team_id" in data


def test_get_current_user_info_unauthorized(client: TestClient):
    """Test getting user info without token fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_info_invalid_token(client: TestClient):
    """Test getting user info with invalid token fails."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_okta_endpoints_not_implemented(client: TestClient):
    """Test Okta endpoints return 501."""
    response = client.get("/api/v1/auth/okta/login")
    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"]
    
    response = client.get("/api/v1/auth/okta/callback")
    assert response.status_code == 501
    assert "not implemented" in response.json()["detail"]
