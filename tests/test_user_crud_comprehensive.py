"""Comprehensive user CRUD tests."""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import User, Organization, Team
from app.schemas import UserRole


class TestUserCRUD:
    """Test user CRUD operations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Create authenticated user and return headers."""
        # Signup
        signup_response = client.post("/api/v1/auth/signup", json={
            "email": "crud@example.com",
            "password": "testpassword123",
            "username": "cruduser",
            "full_name": "CRUD User",
            "organization_name": "CRUD Organization",
            "team_name": "CRUD Team"
        })
        
        token = signup_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def user_info(self, client: TestClient, auth_headers: dict):
        """Get current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        return response.json()

    def test_get_user_by_id_success(self, client: TestClient, auth_headers: dict, user_info: dict):
        """Test getting user by ID."""
        user_id = user_info["id"]
        
        response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "crud@example.com"
        assert data["username"] == "cruduser"
        assert data["full_name"] == "CRUD User"
        assert data["role"] == "admin"

    def test_list_organization_users_success(self, client: TestClient, auth_headers: dict, user_info: dict):
        """Test listing users in organization."""
        org_id = user_info["org_id"]
        
        response = client.get(f"/api/v1/organizations/{org_id}/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data
        assert "has_more" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["email"] == "crud@example.com"

    def test_create_user_success(self, client: TestClient, auth_headers: dict, user_info: dict):
        """Test creating a new user in organization."""
        org_id = user_info["org_id"]
        team_id = user_info["team_id"]
        
        response = client.post(f"/api/v1/organizations/{org_id}/users", json={
            "email": "newuser@example.com",
            "password": "testpassword123",
            "username": "newuser",
            "full_name": "New User",
            "team_id": team_id,
            "role": "member"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["full_name"] == "New User"
        assert data["role"] == "member"
        assert data["org_id"] == org_id
        assert data["team_id"] == team_id