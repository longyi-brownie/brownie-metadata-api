"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Enums
class UserRole(str, Enum):
    """User roles within a team."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class IncidentStatus(str, Enum):
    """Incident status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class IncidentPriority(str, Enum):
    """Incident priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    """Agent types."""
    INCIDENT_RESPONSE = "incident_response"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class PaginationSchema(BaseSchema):
    """Pagination parameters."""

    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    cursor: str | None = Field(default=None, description="Cursor for pagination")


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""

    items: list[Any]
    next_cursor: str | None = None
    has_more: bool = False


class PaginatedUserResponse(BaseSchema):
    """Paginated response wrapper for users."""

    items: list["UserResponse"]
    next_cursor: str | None = None
    has_more: bool = False


# Organization schemas
class OrganizationBase(BaseSchema):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    is_active: bool = True
    max_teams: int = Field(default=10, ge=1)
    max_users_per_team: int = Field(default=50, ge=1)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    is_active: bool | None = None
    max_teams: int | None = Field(None, ge=1)
    max_users_per_team: int | None = Field(None, ge=1)


class OrganizationResponse(OrganizationBase, TimestampSchema):
    """Schema for organization response."""

    id: uuid.UUID


# Team schemas
class TeamBase(BaseSchema):
    """Base team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    is_active: bool = True
    permissions: dict[str, Any] = Field(default_factory=dict)


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    organization_id: uuid.UUID


class TeamUpdate(BaseSchema):
    """Schema for updating a team."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    is_active: bool | None = None
    permissions: dict[str, Any] | None = None


class TeamResponse(TeamBase, TimestampSchema):
    """Schema for team response."""

    id: uuid.UUID
    org_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=500)
    is_active: bool = True
    is_verified: bool = False
    preferences: dict[str, Any] | None = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str | None = Field(None, min_length=8)
    team_id: uuid.UUID
    role: UserRole = UserRole.MEMBER
    organization_id: uuid.UUID


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: str | None = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: str | None = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    is_verified: bool | None = None
    team_id: uuid.UUID | None = None
    role: UserRole | None = None
    preferences: dict[str, Any] | None = None


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response."""

    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    role: UserRole
    organization_id: uuid.UUID
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: uuid.UUID | None = None


# Team member schemas
class TeamMemberAdd(BaseSchema):
    """Schema for adding a team member."""

    user_id: uuid.UUID
    role: UserRole = UserRole.MEMBER


class TeamMemberUpdate(BaseSchema):
    """Schema for updating a team member."""

    role: UserRole


class TeamMemberResponse(BaseSchema):
    """Schema for team member response."""

    user_id: uuid.UUID
    role: UserRole
    user: UserResponse


# Incident schemas
class IncidentBase(BaseSchema):
    """Base incident schema."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    status: IncidentStatus = IncidentStatus.OPEN
    priority: IncidentPriority = IncidentPriority.MEDIUM
    assigned_to: uuid.UUID | None = None
    tags: list[str] = Field(default_factory=list)
    incident_metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""

    team_id: uuid.UUID
    idempotency_key: str | None = Field(None, max_length=255)


class IncidentUpdate(BaseSchema):
    """Schema for updating an incident."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None
    assigned_to: uuid.UUID | None = None
    tags: list[str] | None = None
    incident_metadata: dict[str, Any] | None = None


class IncidentResponse(IncidentBase, TimestampSchema):
    """Schema for incident response."""

    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int
    idempotency_key: str | None = None
    started_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    response_time_minutes: int | None = None
    resolution_time_minutes: int | None = None


class IncidentListParams(PaginationSchema):
    """Parameters for listing incidents."""

    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None
    since: datetime | None = None
    q: str | None = Field(None, description="Search query")


# Agent config schemas
class AgentConfigBase(BaseSchema):
    """Base agent config schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    agent_type: AgentType
    is_active: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    execution_timeout_seconds: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: int = Field(default=60, ge=1)
    triggers: dict[str, Any] = Field(default_factory=dict)
    conditions: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    config_metadata: dict[str, Any] = Field(default_factory=dict)


class AgentConfigCreate(AgentConfigBase):
    """Schema for creating an agent config."""

    team_id: uuid.UUID


class AgentConfigUpdate(BaseSchema):
    """Schema for updating an agent config."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    agent_type: AgentType | None = None
    is_active: bool | None = None
    config: dict[str, Any] | None = None
    execution_timeout_seconds: int | None = Field(None, ge=1)
    max_retries: int | None = Field(None, ge=0)
    retry_delay_seconds: int | None = Field(None, ge=1)
    triggers: dict[str, Any] | None = None
    conditions: dict[str, Any] | None = None
    tags: list[str] | None = None
    config_metadata: dict[str, Any] | None = None


class AgentConfigResponse(AgentConfigBase, TimestampSchema):
    """Schema for agent config response."""

    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    version: int


class AgentConfigListParams(PaginationSchema):
    """Parameters for listing agent configs."""

    agent_type: AgentType | None = None
    is_active: bool | None = None


# Stats schemas
class StatsBase(BaseSchema):
    """Base stats schema."""

    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: str = Field(..., min_length=1, max_length=50)
    value: float
    count: int | None = None
    timestamp: datetime
    time_window: str | None = Field(None, max_length=50)
    labels: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    unit: str | None = Field(None, max_length=50)


class StatsCreate(StatsBase):
    """Schema for creating stats."""

    team_id: uuid.UUID | None = None
    organization_id: uuid.UUID


class StatsResponse(StatsBase, TimestampSchema):
    """Schema for stats response."""

    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID | None = None
    organization_id: uuid.UUID


# Auth schemas
class LoginRequest(BaseSchema):
    """Schema for login request."""

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)


class SignupRequest(BaseSchema):
    """Schema for signup request."""

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: str | None = Field(None, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255)
    team_name: str = Field(..., min_length=1, max_length=255)


class TokenResponse(BaseSchema):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserClaims(BaseSchema):
    """Schema for JWT user claims."""

    user_id: uuid.UUID
    org_id: uuid.UUID
    email: str
    roles: list[str] = Field(default_factory=list)


# Health check schema
class HealthResponse(BaseSchema):
    """Schema for health check response."""

    status: str
    timestamp: datetime
    version: str
    database: str
