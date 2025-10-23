"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


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
    cursor: Optional[str] = Field(default=None, description="Cursor for pagination")


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    
    items: List[Any]
    next_cursor: Optional[str] = None
    has_more: bool = False


class PaginatedUserResponse(BaseSchema):
    """Paginated response wrapper for users."""
    
    items: List[UserResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


# Organization schemas
class OrganizationBase(BaseSchema):
    """Base organization schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    is_active: bool = True
    max_teams: int = Field(default=10, ge=1)
    max_users_per_team: int = Field(default=50, ge=1)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    is_active: Optional[bool] = None
    max_teams: Optional[int] = Field(None, ge=1)
    max_users_per_team: Optional[int] = Field(None, ge=1)


class OrganizationResponse(OrganizationBase, TimestampSchema):
    """Schema for organization response."""
    
    id: uuid.UUID


# Team schemas
class TeamBase(BaseSchema):
    """Base team schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    is_active: bool = True
    permissions: Dict[str, Any] = Field(default_factory=dict)


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    
    organization_id: uuid.UUID


class TeamUpdate(BaseSchema):
    """Schema for updating a team."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None


class TeamResponse(TeamBase, TimestampSchema):
    """Schema for team response."""
    
    id: uuid.UUID
    org_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""
    
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    is_verified: bool = False
    preferences: Optional[Dict[str, Any]] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    
    password: Optional[str] = Field(None, min_length=8)
    team_id: uuid.UUID
    role: UserRole = UserRole.MEMBER
    organization_id: uuid.UUID


class UserUpdate(BaseSchema):
    """Schema for updating a user."""
    
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    team_id: Optional[uuid.UUID] = None
    role: Optional[UserRole] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response."""
    
    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    role: UserRole
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None


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
    description: Optional[str] = None
    status: IncidentStatus = IncidentStatus.OPEN
    priority: IncidentPriority = IncidentPriority.MEDIUM
    assigned_to: Optional[uuid.UUID] = None
    tags: List[str] = Field(default_factory=list)
    incident_metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""
    
    team_id: uuid.UUID
    idempotency_key: Optional[str] = Field(None, max_length=255)


class IncidentUpdate(BaseSchema):
    """Schema for updating an incident."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[IncidentStatus] = None
    priority: Optional[IncidentPriority] = None
    assigned_to: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    incident_metadata: Optional[Dict[str, Any]] = None


class IncidentResponse(IncidentBase, TimestampSchema):
    """Schema for incident response."""
    
    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    version: int
    idempotency_key: Optional[str] = None
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None


class IncidentListParams(PaginationSchema):
    """Parameters for listing incidents."""
    
    status: Optional[IncidentStatus] = None
    priority: Optional[IncidentPriority] = None
    since: Optional[datetime] = None
    q: Optional[str] = Field(None, description="Search query")


# Agent config schemas
class AgentConfigBase(BaseSchema):
    """Base agent config schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: AgentType
    is_active: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    execution_timeout_seconds: int = Field(default=300, ge=1)
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: int = Field(default=60, ge=1)
    triggers: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    config_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfigCreate(AgentConfigBase):
    """Schema for creating an agent config."""
    
    team_id: uuid.UUID


class AgentConfigUpdate(BaseSchema):
    """Schema for updating an agent config."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: Optional[AgentType] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    execution_timeout_seconds: Optional[int] = Field(None, ge=1)
    max_retries: Optional[int] = Field(None, ge=0)
    retry_delay_seconds: Optional[int] = Field(None, ge=1)
    triggers: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    config_metadata: Optional[Dict[str, Any]] = None


class AgentConfigResponse(AgentConfigBase, TimestampSchema):
    """Schema for agent config response."""
    
    id: uuid.UUID
    org_id: uuid.UUID
    team_id: uuid.UUID
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    version: int


class AgentConfigListParams(PaginationSchema):
    """Parameters for listing agent configs."""
    
    agent_type: Optional[AgentType] = None
    is_active: Optional[bool] = None


# Stats schemas
class StatsBase(BaseSchema):
    """Base stats schema."""
    
    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: str = Field(..., min_length=1, max_length=50)
    value: float
    count: Optional[int] = None
    timestamp: datetime
    time_window: Optional[str] = Field(None, max_length=50)
    labels: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=50)


class StatsCreate(StatsBase):
    """Schema for creating stats."""
    
    team_id: Optional[uuid.UUID] = None
    organization_id: uuid.UUID


class StatsResponse(StatsBase, TimestampSchema):
    """Schema for stats response."""
    
    id: uuid.UUID
    org_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
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
    full_name: Optional[str] = Field(None, max_length=255)
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
    roles: List[str] = Field(default_factory=list)


# Health check schema
class HealthResponse(BaseSchema):
    """Schema for health check response."""
    
    status: str
    timestamp: datetime
    version: str
    database: str
