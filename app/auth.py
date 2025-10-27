"""Authentication and authorization utilities."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .db import get_db
from .models import Organization, Team, User, UserRole
from .schemas import LoginRequest, SignupRequest, TokenResponse, UserClaims
from .settings import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT security - auto_error=False to handle missing auth ourselves
security = HTTPBearer(auto_error=False)

# Auth router
router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)  # type: ignore[no-any-return]


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt  # type: ignore[no-any-return]


# --- Role helpers ---
def normalize_role_name(role: Any) -> str:
    """Return a lowercase role name from various role representations.

    Accepts DB enum, schema enum, or raw string.
    """
    try:
        # Enum-like with .value
        value = getattr(role, "value", role)
        return str(value).lower()
    except Exception:
        return str(role).lower()


def to_db_user_role(role: Any) -> UserRole | None:
    """Convert schema enum or string to DB UserRole enum.

    Returns None if role is falsy.
    """
    if role is None:
        return None
    if isinstance(role, UserRole):
        return role
    name = normalize_role_name(role)
    mapping: dict[str, UserRole] = {}
    # Build mapping from DB enum values/names in a tolerant way
    try:
        mapping = {
            "admin": UserRole.ADMIN,  # type: ignore[attr-defined]
            "member": getattr(UserRole, "MEMBER", None),
            "viewer": UserRole.VIEWER,  # type: ignore[attr-defined]
            "editor": getattr(UserRole, "EDITOR", None),
        }
    except Exception:
        # Fallback: best-effort name-based resolution
        pass

    resolved = mapping.get(name)
    if resolved is not None:
        return resolved
    # Last resort: try attribute lookup by uppercased name
    try:
        return getattr(UserRole, name.upper())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}",
        ) from e


def verify_token(token: str) -> UserClaims | None:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        email: str = payload.get("email")
        roles: list = payload.get("roles", [])

        if user_id is None or org_id is None or email is None:
            return None

        return UserClaims(
            user_id=uuid.UUID(user_id),
            org_id=uuid.UUID(org_id),
            email=email,
            roles=roles,
        )
    except (JWTError, ValueError) as e:
        logger.warning("Invalid token", error=str(e))
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        claims = verify_token(token)
        if claims is None:
            raise credentials_exception

        user = (
            db.query(User)
            .filter(
                User.id == claims.user_id, User.is_active, User.deleted_at.is_(None)
            )
            .first()
        )

        if user is None:
            raise credentials_exception

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Authentication failed", error=str(e))
        raise credentials_exception from e


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserClaims:
    """Get the current user's JWT claims."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        claims = verify_token(token)
        if claims is None:
            raise credentials_exception
        return claims
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Token validation failed", error=str(e))
        raise credentials_exception from e


def require_team_role(team_id: uuid.UUID, allowed_roles: set[str]) -> Any:
    """Create a dependency that requires specific team roles."""

    async def check_team_role(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        """Check if user has required role in the team."""

        # Check if user belongs to the team
        if current_user.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to this team",
            )

        # Check if user has required role (normalize to lowercase)
        normalized_allowed = {r.lower() for r in allowed_roles}
        current_role = current_user.role.value.lower() if current_user.role else ""
        if current_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_role}' not in allowed roles: {normalized_allowed}",
            )

        return current_user

    return check_team_role


def require_permission(permission: str) -> Any:
    """Create a dependency that requires a specific permission."""

    async def check_permission(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        """Check if user has the required permission."""

        # Get user's team to check permissions
        team = db.query(Team).filter(Team.id == current_user.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User team not found"
            )

        # Check role-based permissions
        user_permissions = _get_role_permissions(current_user.role)

        # Check team-specific permissions
        team_permissions = team.permissions or {}
        user_permissions.update(team_permissions.get(str(current_user.id), {}))

        if permission not in user_permissions or not user_permissions[permission]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return current_user

    return check_permission


def _get_role_permissions(role: UserRole) -> dict:
    """Get permissions for a user role."""
    permissions = {
        "admin": {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": True,
            "manage_teams": True,
            "manage_organizations": True,
            "manage_incidents": True,
            "manage_agent_configs": True,
            "manage_stats": True,
        },
        "editor": {
            "read": True,
            "write": True,
            "delete": False,
            "manage_users": False,
            "manage_teams": False,
            "manage_organizations": False,
            "manage_incidents": True,
            "manage_agent_configs": True,
            "manage_stats": True,
        },
        "viewer": {
            "read": True,
            "write": False,
            "delete": False,
            "manage_users": False,
            "manage_teams": False,
            "manage_organizations": False,
            "manage_incidents": False,
            "manage_agent_configs": False,
            "manage_stats": False,
        },
    }

    key = role.value.lower() if hasattr(role, "value") else str(role).lower()
    return permissions.get(key, {})


def require_org_access(org_id: uuid.UUID) -> Any:
    """Create a dependency that requires organization access."""

    async def check_org_access(current_user: User = Depends(get_current_user)) -> User:
        """Check if user belongs to the organization."""

        if current_user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to this organization",
            )

        return current_user

    return check_org_access


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user with email and password."""
    user = (
        db.query(User)
        .filter(User.email == email, User.is_active, User.deleted_at.is_(None))
        .first()
    )

    if not user:
        return None

    if not user.password_hash or not verify_password(password, user.password_hash):
        return None

    return user


def create_user_token(user: User) -> str:
    """Create a JWT token for a user."""
    roles = [user.role.value.lower()] if user.role else []

    token_data = {
        "sub": str(user.id),
        "org_id": str(user.org_id),
        "email": user.email,
        "roles": roles,
        "iat": datetime.now(UTC),
    }

    return create_access_token(token_data)


# Auth endpoints
@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_user_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expires_minutes * 60,
    )


@router.post("/signup", response_model=TokenResponse)
async def signup(signup_data: SignupRequest, db: Session = Depends(get_db)):
    """Sign up a new user and create organization/team."""

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create organization
    org_slug = signup_data.organization_name.lower().replace(" ", "-")
    organization = Organization(
        name=signup_data.organization_name,
        slug=org_slug,
        is_active=True,
        max_teams=10,
        max_users_per_team=50,
    )
    db.add(organization)
    db.flush()  # Get the org ID

    # Create team
    team_slug = signup_data.team_name.lower().replace(" ", "-")
    team = Team(
        name=signup_data.team_name,
        slug=team_slug,
        org_id=organization.id,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(team)
    db.flush()  # Get the team ID

    # Create user
    user = User(
        email=signup_data.email,
        username=signup_data.username,
        full_name=signup_data.full_name,
        password_hash=get_password_hash(signup_data.password),
        is_active=True,
        is_verified=False,
        team_id=team.id,
        role=UserRole.ADMIN,  # First user is admin
        org_id=organization.id,
        organization_id=organization.id,
    )
    db.add(user)
    db.commit()

    access_token = create_user_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expires_minutes * 60,
    )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value.lower() if current_user.role else None,
        "org_id": current_user.org_id,
        "team_id": current_user.team_id,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
    }


# Okta OIDC stubs (for v1)
@router.get("/okta/login")
async def okta_login():
    """Stub for Okta OIDC login."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Okta OIDC integration not implemented in v1",
    )


@router.get("/okta/callback")
async def okta_callback():
    """Stub for Okta OIDC callback."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Okta OIDC integration not implemented in v1",
    )
