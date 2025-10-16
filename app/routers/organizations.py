"""Organization management endpoints."""

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_org_access
from ..db import get_db
from ..models import Organization, User
from ..schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    
    # Check if organization with same name/slug exists
    existing_org = db.query(Organization).filter(
        (Organization.name == org_data.name) | (Organization.slug == org_data.slug)
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name or slug already exists"
        )
    
    # Create organization
    organization = Organization(
        name=org_data.name,
        slug=org_data.slug,
        description=org_data.description,
        is_active=org_data.is_active,
        max_teams=org_data.max_teams,
        max_users_per_team=org_data.max_users_per_team,
    )
    
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    logger.info(
        "Organization created",
        organization_id=organization.id,
        name=organization.name,
        created_by=current_user.id
    )
    
    return organization


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(require_org_access(org_id)),
    db: Session = Depends(get_db)
):
    """Get organization by ID."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    org_data: OrganizationUpdate,
    current_user: User = Depends(require_org_access(org_id)),
    db: Session = Depends(get_db)
):
    """Update organization."""
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    logger.info(
        "Organization updated",
        organization_id=organization.id,
        updated_by=current_user.id
    )
    
    return organization


@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organizations accessible to current user."""
    
    # For now, users can only see their own organization
    # In a multi-org setup, this would be more complex
    organizations = db.query(Organization).filter(
        Organization.id == current_user.org_id
    ).all()
    
    return organizations
