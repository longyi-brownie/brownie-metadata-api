"""Comprehensive user CRUD tests."""

import time
import uuid

import pytest


def make_unique(base: str) -> str:
    """Generate unique string for test data."""
    return f"{base}-{uuid.uuid4().hex[:8]}-{int(time.time() * 1000) % 100000}"


class TestUserCRUD:
    """Test user CRUD operations."""

    @pytest.fixture
    def auth_headers(self, client):
        """Create authenticated user and return headers."""
        # Signup
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": make_unique("crud") + "@example.com",
                "password": "testpassword123",
                "username": make_unique("cruduser"),
                "full_name": "CRUD User",
                "organization_name": make_unique("CRUD Organization"),
                "team_name": make_unique("CRUD Team"),
            },
        )

        token = signup_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def user_info(self, client, auth_headers):
        """Get current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        return response.json()

    def test_get_user_by_id_success(self, client, auth_headers, user_info):
        """Test getting user by ID."""
        user_id = user_info["id"]

        response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert "@example.com" in data["email"]
        assert "cruduser" in data["username"]
        assert data["full_name"] == "CRUD User"
        assert data["role"] == "admin"

    def test_list_organization_users_success(self, client, auth_headers, user_info):
        """Test listing users in organization."""
        org_id = user_info["org_id"]

        response = client.get(
            f"/api/v1/organizations/{org_id}/users", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data
        assert "has_more" in data
        assert len(data["items"]) == 1
        assert "@example.com" in data["items"][0]["email"]

    def test_create_user_success(self, client, auth_headers, user_info):
        """Test creating a new user in organization."""
        org_id = user_info["org_id"]
        team_id = user_info["team_id"]

        new_email = make_unique("newuser") + "@example.com"
        new_username = make_unique("newuser")
        response = client.post(
            f"/api/v1/organizations/{org_id}/users",
            json={
                "email": new_email,
                "password": "testpassword123",
                "username": new_username,
                "full_name": "New User",
                "organization_id": org_id,
                "team_id": team_id,
                "role": "member",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email
        assert data["username"] == new_username
        assert data["full_name"] == "New User"
        assert data["role"] == "member"
        assert data["org_id"] == org_id
        assert data["team_id"] == team_id
