"""Test incident endpoints."""

from fastapi.testclient import TestClient


def test_create_incident(client: TestClient, test_user_data, test_incident_data):
    """Test creating an incident (editor/admin only)."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    response = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == test_incident_data["title"]
    assert data["description"] == test_incident_data["description"]
    assert data["status"] == test_incident_data["status"]
    assert data["priority"] == test_incident_data["priority"]
    assert data["team_id"] == team_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_incident_with_idempotency_key(client: TestClient, test_user_data, test_incident_data):
    """Test creating incident with idempotency key."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident with idempotency key
    incident_data = {
        **test_incident_data,
        "team_id": team_id,
        "idempotency_key": "test-key-123"
    }

    # First creation
    response1 = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    assert response1.status_code == 200

    # Second creation with same idempotency key should return same incident
    response2 = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    assert response2.status_code == 200
    assert response1.json()["id"] == response2.json()["id"]


def test_list_incidents(client: TestClient, test_user_data, test_incident_data):
    """Test listing incidents with filters and pagination."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)

    # List incidents
    response = client.get(f"/api/v1/teams/{team_id}/incidents", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "has_more" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


def test_list_incidents_with_filters(client: TestClient, test_user_data, test_incident_data):
    """Test listing incidents with status filter."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)

    # List incidents with status filter
    response = client.get(
        f"/api/v1/teams/{team_id}/incidents?status=open",
        headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert all(incident["status"] == "open" for incident in data["items"])


def test_get_incident(client: TestClient, test_user_data, test_incident_data):
    """Test getting an incident by ID."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    create_response = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    incident_id = create_response.json()["id"]

    # Get incident
    response = client.get(f"/api/v1/incidents/{incident_id}", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == incident_id
    assert data["title"] == test_incident_data["title"]


def test_update_incident(client: TestClient, test_user_data, test_incident_data):
    """Test updating an incident (editor/admin only)."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    create_response = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    incident_id = create_response.json()["id"]

    # Update incident
    update_data = {
        "title": "Updated Incident",
        "status": "in_progress"
    }
    response = client.put(f"/api/v1/incidents/{incident_id}", json=update_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["status"] == update_data["status"]


def test_delete_incident(client: TestClient, test_user_data, test_incident_data):
    """Test deleting an incident (admin only)."""
    # Signup to get token and team
    signup_response = client.post("/api/v1/auth/signup", json=test_user_data)
    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get user info to get team_id
    user_response = client.get("/api/v1/auth/me", headers=headers)
    team_id = user_response.json()["team_id"]

    # Create incident
    incident_data = {**test_incident_data, "team_id": team_id}
    create_response = client.post(f"/api/v1/teams/{team_id}/incidents", json=incident_data, headers=headers)
    incident_id = create_response.json()["id"]

    # Delete incident
    response = client.delete(f"/api/v1/incidents/{incident_id}", headers=headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]
