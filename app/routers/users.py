"""User management endpoints."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Organization, Team, User
from ..schemas import (
    PaginatedUserResponse,
    PaginationSchema,
    UserCreate,
    UserResponse,
    UserUpdate,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/organizations/{org_id}/users", response_model=UserResponse)
async def create_user(
    org_id: uuid.UUID,
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user in an organization."""

    # Check organization access
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Verify team exists and belongs to org
    team = (
        db.query(Team)
        .filter(Team.id == user_data.team_id, Team.org_id == org_id)
        .first()
    )
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or does not belong to organization",
        )

    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter((User.email == user_data.email) | (User.username == user_data.username))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )

    # Hash password if provided
    password_hash = None
    if user_data.password:
        from ..auth import get_password_hash

        password_hash = get_password_hash(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        avatar_url=user_data.avatar_url,
        password_hash=password_hash,
        is_active=user_data.is_active,
        is_verified=user_data.is_verified,
        team_id=user_data.team_id,
        role=user_data.role,
        preferences=user_data.preferences,
        org_id=org_id,
        organization_id=org_id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        "User created",
        user_id=user.id,
        email=user.email,
        org_id=org_id,
        team_id=user_data.team_id,
        created_by=current_user.id,
    )

    return user


@router.get("/organizations/{org_id}/users", response_model=PaginatedUserResponse)
async def list_users(
    org_id: uuid.UUID,
    pagination: PaginationSchema = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List users in an organization with pagination."""

    # Check organization access
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )

    query = db.query(User).filter(User.org_id == org_id, User.deleted_at.is_(None))

    # Apply cursor pagination
    if pagination.cursor:
        try:
            cursor_id = uuid.UUID(pagination.cursor)
            query = query.filter(User.id > cursor_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor format"
            ) from e

    # Get users
    users = query.order_by(User.id).limit(pagination.limit + 1).all()

    # Check if there are more results
    has_more = len(users) > pagination.limit
    if has_more:
        users = users[:-1]

    # Get next cursor
    next_cursor = str(users[-1].id) if users and has_more else None

    return PaginatedUserResponse(
        items=users, next_cursor=next_cursor, has_more=has_more
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user by ID."""

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user belongs to same organization
    if current_user.org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to the same organization",
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user (users can update themselves, admins can update anyone in their team)."""

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check permissions
    if current_user.id != user_id:
        # Check if current user is admin in the same team
        if current_user.team_id != user.team_id or current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this user",
            )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            # Hash new password
            from ..auth import get_password_hash

            user.password_hash = get_password_hash(value)
        else:
            setattr(user, field, value)

    user.updated_by = current_user.id
    db.commit()
    db.refresh(user)

    logger.info("User updated", user_id=user.id, updated_by=current_user.id)

    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete user (admin only)."""

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if current user is admin in the same team
    if current_user.team_id != user.team_id or current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this user",
        )

    # Don't allow deleting the last admin
    if user.role.value == "admin":
        admin_count = (
            db.query(User)
            .filter(
                User.team_id == user.team_id,
                User.role == "admin",
                User.is_active,
                User.deleted_at.is_(None),
            )
            .count()
        )

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin from team",
            )

    # Soft delete user
    user.deleted_at = db.func.now()
    user.deleted_by = current_user.id
    user.is_active = False

    db.commit()

    logger.info("User deleted", user_id=user.id, deleted_by=current_user.id)

    return {"message": "User deleted successfully"}
