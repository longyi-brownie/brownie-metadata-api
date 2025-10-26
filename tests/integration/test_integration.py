"""Integration tests with real database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app


class TestIntegration:
    """Integration tests with real database."""

    def test_full_user_lifecycle(self, client: TestClient, test_db_session: Session):
        """Test complete user lifecycle from signup to deletion."""
        # 1. Signup
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "lifecycle@example.com",
                "password": "testpassword123",
                "username": "lifecycleuser",
                "full_name": "Lifecycle User",
                "organization_name": "Lifecycle Organization",
                "team_name": "Lifecycle Team",
            },
        )

        assert signup_response.status_code == 200
        token = signup_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get current user
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        user_id = user_data["id"]
        org_id = user_data["org_id"]
        team_id = user_data["team_id"]

        # 3. Get user by ID
        user_response = client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert user_response.status_code == 200
        assert user_response.json()["email"] == "lifecycle@example.com"

        # 4. List organization users
        org_users_response = client.get(
            f"/api/v1/organizations/{org_id}/users", headers=headers
        )
        assert org_users_response.status_code == 200
        assert len(org_users_response.json()["items"]) == 1

        # 5. Create another user in same organization
        create_user_response = client.post(
            f"/api/v1/organizations/{org_id}/users",
            json={
                "email": "second@example.com",
                "password": "testpassword123",
                "username": "seconduser",
                "full_name": "Second User",
                "team_id": team_id,
                "role": "member",
            },
            headers=headers,
        )

        assert create_user_response.status_code == 200
        second_user_id = create_user_response.json()["id"]

        # 6. Verify both users in organization
        org_users_response = client.get(
            f"/api/v1/organizations/{org_id}/users", headers=headers
        )
        assert org_users_response.status_code == 200
        assert len(org_users_response.json()["items"]) == 2

        # 7. Update user
        update_response = client.put(
            f"/api/v1/users/{second_user_id}",
            json={
                "full_name": "Updated Second User",
                "avatar_url": "https://example.com/avatar.jpg",
            },
            headers=headers,
        )

        assert update_response.status_code == 200
        assert update_response.json()["full_name"] == "Updated Second User"

        # 8. Delete user
        delete_response = client.delete(
            f"/api/v1/users/{second_user_id}", headers=headers
        )
        assert delete_response.status_code == 200

        # 9. Verify user is deleted (soft delete)
        org_users_response = client.get(
            f"/api/v1/organizations/{org_id}/users", headers=headers
        )
        assert org_users_response.status_code == 200
        assert len(org_users_response.json()["items"]) == 1

        # 10. Verify deleted user cannot be accessed
        deleted_user_response = client.get(
            f"/api/v1/users/{second_user_id}", headers=headers
        )
        assert deleted_user_response.status_code == 404

    def test_multi_organization_isolation(
        self, client: TestClient, test_db_session: Session
    ):
        """Test that users from different organizations are properly isolated."""
        # Create two users in different organizations
        signup1 = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "org1@example.com",
                "password": "testpassword123",
                "username": "org1user",
                "full_name": "Org1 User",
                "organization_name": "Organization 1",
                "team_name": "Team 1",
            },
        )

        signup2 = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "org2@example.com",
                "password": "testpassword123",
                "username": "org2user",
                "full_name": "Org2 User",
                "organization_name": "Organization 2",
                "team_name": "Team 2",
            },
        )

        token1 = signup1.json()["access_token"]
        token2 = signup2.json()["access_token"]

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Get user info
        user1 = client.get("/api/v1/auth/me", headers=headers1)
        user2 = client.get("/api/v1/auth/me", headers=headers2)

        user1_data = user1.json()
        user2_data = user2.json()

        org1_id = user1_data["org_id"]
        org2_id = user2_data["org_id"]

        # Verify different organizations
        assert org1_id != org2_id

        # User 1 cannot access User 2's data
        user2_access = client.get(f"/api/v1/users/{user2_data['id']}", headers=headers1)
        assert user2_access.status_code == 403

        # User 1 cannot list User 2's organization users
        org2_users = client.get(
            f"/api/v1/organizations/{org2_id}/users", headers=headers1
        )
        assert org2_users.status_code == 403

        # User 2 cannot access User 1's data
        user1_access = client.get(f"/api/v1/users/{user1_data['id']}", headers=headers2)
        assert user1_access.status_code == 403

        # User 2 cannot list User 1's organization users
        org1_users = client.get(
            f"/api/v1/organizations/{org1_id}/users", headers=headers2
        )
        assert org1_users.status_code == 403

    def test_authentication_flow(self, client: TestClient, test_db_session: Session):
        """Test complete authentication flow."""
        # 1. Signup
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "auth@example.com",
                "password": "testpassword123",
                "username": "authuser",
                "full_name": "Auth User",
                "organization_name": "Auth Organization",
                "team_name": "Auth Team",
            },
        )

        assert signup_response.status_code == 200
        token = signup_response.json()["access_token"]

        # 2. Login with same credentials
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "auth@example.com", "password": "testpassword123"},
        )

        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # 3. Both tokens should work
        headers1 = {"Authorization": f"Bearer {token}"}
        headers2 = {"Authorization": f"Bearer {login_token}"}

        me1 = client.get("/api/v1/auth/me", headers=headers1)
        me2 = client.get("/api/v1/auth/me", headers=headers2)

        assert me1.status_code == 200
        assert me2.status_code == 200
        assert me1.json()["email"] == me2.json()["email"]

        # 4. Login with wrong password should fail
        wrong_login = client.post(
            "/api/v1/auth/login",
            json={"email": "auth@example.com", "password": "wrongpassword"},
        )

        assert wrong_login.status_code == 401

    def test_pagination(self, client: TestClient, test_db_session: Session):
        """Test pagination functionality."""
        # Create a user and organization
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "pagination@example.com",
                "password": "testpassword123",
                "username": "paginationuser",
                "full_name": "Pagination User",
                "organization_name": "Pagination Organization",
                "team_name": "Pagination Team",
            },
        )

        token = signup_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        user_data = client.get("/api/v1/auth/me", headers=headers).json()
        org_id = user_data["org_id"]
        team_id = user_data["team_id"]

        # Create multiple users
        for i in range(10):
            client.post(
                f"/api/v1/organizations/{org_id}/users",
                json={
                    "email": f"user{i}@example.com",
                    "password": "testpassword123",
                    "username": f"user{i}",
                    "full_name": f"User {i}",
                    "team_id": team_id,
                    "role": "member",
                },
                headers=headers,
            )

        # Test pagination
        response = client.get(
            f"/api/v1/organizations/{org_id}/users?limit=5", headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 5
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

        # Test next page
        next_response = client.get(
            f"/api/v1/organizations/{org_id}/users?limit=5&cursor={data['next_cursor']}",
            headers=headers,
        )
        assert next_response.status_code == 200

        next_data = next_response.json()
        assert len(next_data["items"]) == 5
        assert next_data["has_more"] is True

    def test_error_handling(self, client: TestClient, test_db_session: Session):
        """Test error handling scenarios."""
        # Test invalid endpoints
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # Test invalid UUID
        response = client.get("/api/v1/users/invalid-uuid")
        assert response.status_code == 422

        # Test unauthorized access
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

        # Test invalid token
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_database_consistency(self, client: TestClient, test_db_session: Session):
        """Test database consistency and constraints."""
        # Test duplicate email signup
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "username": "duplicate1",
                "full_name": "Duplicate User 1",
                "organization_name": "Duplicate Organization 1",
                "team_name": "Duplicate Team 1",
            },
        )

        duplicate_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "username": "duplicate2",
                "full_name": "Duplicate User 2",
                "organization_name": "Duplicate Organization 2",
                "team_name": "Duplicate Team 2",
            },
        )

        assert duplicate_response.status_code == 400

        # Test duplicate username in same organization
        signup_response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "consistency@example.com",
                "password": "testpassword123",
                "username": "consistencyuser",
                "full_name": "Consistency User",
                "organization_name": "Consistency Organization",
                "team_name": "Consistency Team",
            },
        )

        token = signup_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        user_data = client.get("/api/v1/auth/me", headers=headers).json()
        org_id = user_data["org_id"]
        team_id = user_data["team_id"]

        # Try to create user with same username in same org
        duplicate_username = client.post(
            f"/api/v1/organizations/{org_id}/users",
            json={
                "email": "different@example.com",
                "password": "testpassword123",
                "username": "consistencyuser",  # Same username
                "full_name": "Different User",
                "team_id": team_id,
                "role": "member",
            },
            headers=headers,
        )

        assert duplicate_username.status_code == 400
