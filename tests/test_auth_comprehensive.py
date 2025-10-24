"""Comprehensive authentication tests."""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import User, Organization, Team
from app.schemas import UserRole


class TestAuthentication:
    """Test authentication functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_org(self, db: Session):
        """Create test organization."""
        org = Organization(
            id=uuid.uuid4(),
            name="Test Organization",
            slug="test-org",
            description="Test organization for testing"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @pytest.fixture
    def test_team(self, db: Session, test_org: Organization):
        """Create test team."""
        team = Team(
            id=uuid.uuid4(),
            name="Test Team",
            description="Test team for testing",
            org_id=test_org.id
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    def test_signup_success(self, client: TestClient, test_org: Organization, test_team: Team):
        """Test successful user signup."""
        response = client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "testpassword123",
            "username": "testuser",
            "full_name": "Test User",
            "organization_name": "New Test Organization",
            "team_name": "New Test Team"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_login_success(self, client: TestClient):
        """Test successful login."""
        # First signup
        client.post("/api/v1/auth/signup", json={
            "email": "login@example.com",
            "password": "testpassword123",
            "username": "loginuser",
            "full_name": "Login User",
            "organization_name": "Login Organization",
            "team_name": "Login Team"
        })
        
        # Then login
        response = client.post("/api/v1/auth/login", json={
            "email": "login@example.com",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_get_current_user_success(self, client: TestClient):
        """Test getting current user with valid token."""
        # Signup
        signup_response = client.post("/api/v1/auth/signup", json={
            "email": "current@example.com",
            "password": "testpassword123",
            "username": "currentuser",
            "full_name": "Current User",
            "organization_name": "Current Organization",
            "team_name": "Current Team"
        })
        
        token = signup_response.json()["access_token"]
        
        # Get current user
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["username"] == "currentuser"
        assert data["full_name"] == "Current User"
        assert data["role"] == "admin"