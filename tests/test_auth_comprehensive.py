"""Comprehensive authentication tests."""

import time
import uuid


class TestAuthentication:
    """Test authentication functionality."""

    def test_signup_success(self, client):
        """Test successful user signup."""
        unique = f"{uuid.uuid4().hex[:8]}-{int(time.time() * 1000) % 100000}"
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"test-{unique}@example.com",
                "password": "testpassword123",
                "username": f"testuser-{unique}",
                "full_name": "Test User",
                "organization_name": f"New Test Organization {unique}",
                "team_name": f"New Test Team {unique}",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_login_success(self, client):
        """Test successful login."""
        unique = f"{uuid.uuid4().hex[:8]}-{int(time.time() * 1000) % 100000}"
        email = f"login-{unique}@example.com"
        # First signup
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "testpassword123",
                "username": f"loginuser-{unique}",
                "full_name": "Login User",
                "organization_name": f"Login Organization {unique}",
                "team_name": f"Login Team {unique}",
            },
        )

        # Then login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_get_current_user_success(self, client):
        """Test getting current user with valid token."""
        unique = f"{uuid.uuid4().hex[:8]}-{int(time.time() * 1000) % 100000}"
        email = f"current-{unique}@example.com"
        username = f"currentuser-{unique}"
        # Signup
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "testpassword123",
                "username": username,
                "full_name": "Current User",
                "organization_name": f"Current Organization {unique}",
                "team_name": f"Current Team {unique}",
            },
        )

        token = signup_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["username"] == username
        assert data["full_name"] == "Current User"
        assert data["role"] == "admin"
