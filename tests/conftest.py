"""Test configuration and fixtures."""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.models import Base
from app.db import get_db
from app.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def test_db_url(postgres_container):
    """Get test database URL."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create test database engine."""
    engine = create_engine(test_db_url)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db_session(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_db_session):
    """Create test client with database session override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "username": "testuser",
        "full_name": "Test User",
        "organization_name": "Test Organization",
        "team_name": "Test Team"
    }


@pytest.fixture
def test_organization_data():
    """Test organization data."""
    return {
        "name": "Test Organization",
        "slug": "test-org",
        "description": "A test organization",
        "is_active": True,
        "max_teams": 10,
        "max_users_per_team": 50
    }


@pytest.fixture
def test_team_data():
    """Test team data."""
    return {
        "name": "Test Team",
        "slug": "test-team",
        "description": "A test team",
        "is_active": True,
        "permissions": {}
    }


@pytest.fixture
def test_incident_data():
    """Test incident data."""
    return {
        "title": "Test Incident",
        "description": "A test incident",
        "status": "open",
        "priority": "medium",
        "tags": ["test", "incident"],
        "incident_metadata": {"test": True}
    }


@pytest.fixture
def test_agent_config_data():
    """Test agent config data."""
    return {
        "name": "Test Agent",
        "description": "A test agent configuration",
        "agent_type": "incident_response",
        "is_active": True,
        "config": {"test": True},
        "execution_timeout_seconds": 300,
        "max_retries": 3,
        "retry_delay_seconds": 60,
        "triggers": {},
        "conditions": {},
        "tags": ["test"],
        "config_metadata": {}
    }


@pytest.fixture
def test_stats_data():
    """Test stats data."""
    return {
        "metric_name": "test_metric",
        "metric_type": "counter",
        "value": 1.0,
        "count": 1,
        "timestamp": "2023-01-01T00:00:00Z",
        "time_window": "1m",
        "labels": {"test": True},
        "description": "A test metric",
        "unit": "count"
    }
