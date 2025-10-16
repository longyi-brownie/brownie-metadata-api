"""Test organization endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_create_organization(client: TestClient, test_user_data, test_organization_data):
    """Test creating an organization."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    response = client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == test_organization_data["name"]
    assert data["slug"] == test_organization_data["slug"]
    assert data["description"] == test_organization_data["description"]
    assert data["is_active"] == test_organization_data["is_active"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_organization_duplicate_name(client: TestClient, test_user_data, test_organization_data):
    """Test creating organization with duplicate name fails."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create first organization
    client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    
    # Try to create second organization with same name
    response = client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_organization(client: TestClient, test_user_data, test_organization_data):
    """Test getting an organization by ID."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    create_response = client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    org_id = create_response.json()["id"]
    
    # Get organization
    response = client.get(f"/api/v1/organizations/{org_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == org_id
    assert data["name"] == test_organization_data["name"]


def test_get_organization_not_found(client: TestClient, test_user_data):
    """Test getting nonexistent organization returns 404."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get nonexistent organization
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/organizations/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_organization(client: TestClient, test_user_data, test_organization_data):
    """Test updating an organization."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    create_response = client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    org_id = create_response.json()["id"]
    
    # Update organization
    update_data = {
        "name": "Updated Organization",
        "description": "Updated description"
    }
    response = client.put(f"/api/v1/organizations/{org_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


def test_list_organizations(client: TestClient, test_user_data, test_organization_data):
    """Test listing organizations."""
    # Signup to get token
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create organization
    client.post("/api/v1/organizations", json=test_organization_data, headers=headers)
    
    # List organizations
    response = client.get("/api/v1/organizations", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the one we created
    assert any(org["name"] == test_organization_data["name"] for org in data)
