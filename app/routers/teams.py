"""Team management endpoints."""

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_org_access, require_team_role
from ..db import get_db
from ..models import Team, User, Organization
from ..schemas import TeamCreate, TeamResponse, TeamUpdate, TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/organizations/{org_id}/teams", response_model=TeamResponse)
async def create_team(
    org_id: uuid.UUID,
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new team under an organization."""
    
    # Check organization access
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if team with same name/slug exists in org
    existing_team = db.query(Team).filter(
        Team.org_id == org_id,
        (Team.name == team_data.name) | (Team.slug == team_data.slug)
    ).first()
    
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this name or slug already exists in organization"
        )
    
    # Create team
    team = Team(
        name=team_data.name,
        slug=team_data.slug,
        description=team_data.description,
        is_active=team_data.is_active,
        permissions=team_data.permissions,
        org_id=org_id,
        organization_id=org_id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    logger.info(
        "Team created",
        team_id=team.id,
        name=team.name,
        org_id=org_id,
        created_by=current_user.id
    )
    
    return team


@router.get("/organizations/{org_id}/teams", response_model=List[TeamResponse])
async def list_teams(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List teams in an organization."""
    
    # Check organization access
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    teams = db.query(Team).filter(
        Team.org_id == org_id,
        Team.is_active == True
    ).all()
    
    return teams


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team by ID."""
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check team access
    if team.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team's organization"
        )
    
    return team


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team (admin only)."""
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check team access
    if team.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team's organization"
        )
    
    # Update fields
    update_data = team_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    
    team.updated_by = current_user.id
    db.commit()
    db.refresh(team)
    
    logger.info(
        "Team updated",
        team_id=team.id,
        updated_by=current_user.id
    )
    
    return team


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: uuid.UUID,
    member_data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to a team (admin only)."""
    
    # Get team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check team membership
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )
    
    # Check role permissions (admin only)
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    
    # Get user to add
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user belongs to same organization
    if user.org_id != team.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to the same organization"
        )
    
    # Update user's team and role
    user.team_id = team_id
    user.role = member_data.role
    user.updated_by = current_user.id
    
    db.commit()
    db.refresh(user)
    
    logger.info(
        "Team member added",
        team_id=team_id,
        user_id=user.id,
        role=member_data.role.value,
        added_by=current_user.id
    )
    
    return TeamMemberResponse(
        user_id=user.id,
        role=user.role,
        user=user
    )


@router.put("/teams/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    member_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update team member role (admin only)."""
    
    # Check team membership
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )
    
    # Check role permissions (admin only)
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.team_id == team_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in team"
        )
    
    # Update role
    user.role = member_data.role
    user.updated_by = current_user.id
    
    db.commit()
    db.refresh(user)
    
    logger.info(
        "Team member updated",
        team_id=team_id,
        user_id=user.id,
        new_role=member_data.role.value,
        updated_by=current_user.id
    )
    
    return TeamMemberResponse(
        user_id=user.id,
        role=user.role,
        user=user
    )


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove member from team (admin only)."""
    
    # Check team membership
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )
    
    # Check role permissions (admin only)
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    
    # Get user
    user = db.query(User).filter(
        User.id == user_id,
        User.team_id == team_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in team"
        )
    
    # Don't allow removing the last admin
    if user.role.value == "admin":
        admin_count = db.query(User).filter(
            User.team_id == team_id,
            User.role == "admin",
            User.is_active == True,
            User.deleted_at.is_(None)
        ).count()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin from team"
            )
    
    # Soft delete user
    user.deleted_at = db.func.now()
    user.deleted_by = current_user.id
    user.is_active = False
    
    db.commit()
    
    logger.info(
        "Team member removed",
        team_id=team_id,
        user_id=user.id,
        removed_by=current_user.id
    )
    
    return {"message": "Team member removed successfully"}
