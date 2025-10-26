"""Minimal model definitions for FastAPI app to work without database package dependency."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)


class OrgScopedMixin:
    """Mixin for organization-scoped entities."""

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Organization ID for multi-tenancy",
    )


class AuditMixin:
    """Mixin for audit logging on mutations."""

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who created this record",
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who last updated this record",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime] = mapped_column(nullable=True)
    deleted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who soft deleted this record",
    )


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""

    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


# Enums
class UserRole(str, enum.Enum):
    """User roles within a team."""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class IncidentStatus(str, enum.Enum):
    """Incident status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentPriority(str, enum.Enum):
    """Incident priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, enum.Enum):
    """Agent configuration types."""

    MONITORING = "monitoring"
    ALERTING = "alerting"
    AUTOMATION = "automation"


# Models
class Organization(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Organization model."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    teams = relationship("Team", back_populates="organization")
    users = relationship("User", back_populates="organization")


class Team(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Team model."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    users = relationship("User", back_populates="team")


class User(BaseModel, TimestampMixin, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """User model for team members."""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Auth
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OIDC/SSO
    oidc_subject: Mapped[str] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    oidc_provider: Mapped[str] = mapped_column(String(100), nullable=True)

    # Team membership
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER, nullable=False
    )

    # Settings
    preferences: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="users")


class Incident(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Incident model."""

    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        Enum(IncidentPriority), default=IncidentPriority.MEDIUM, nullable=False
    )

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


class AgentConfig(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Agent configuration model."""

    __tablename__ = "agent_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class Stats(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Statistics model."""

    __tablename__ = "stats"

    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    metric_unit: Mapped[str] = mapped_column(String(50), nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class Config(BaseModel, OrgScopedMixin, AuditMixin, SoftDeleteMixin):
    """Configuration model."""

    __tablename__ = "configs"

    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
