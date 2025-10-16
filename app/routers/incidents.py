"""Incident management endpoints."""

import uuid
from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..auth import get_current_user, require_team_role
from ..db import get_db
from ..models import Incident, Team, User
from ..schemas import (
    IncidentCreate, IncidentResponse, IncidentUpdate, 
    IncidentListParams, PaginatedResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/teams/{team_id}/incidents", response_model=IncidentResponse)
async def create_incident(
    team_id: uuid.UUID,
    incident_data: IncidentCreate,
    current_user: User = Depends(require_team_role(team_id, {"editor", "admin"})),
    db: Session = Depends(get_db)
):
    """Create a new incident (editor/admin only)."""
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check for idempotency key if provided
    if incident_data.idempotency_key:
        existing_incident = db.query(Incident).filter(
            Incident.idempotency_key == incident_data.idempotency_key
        ).first()
        
        if existing_incident:
            return existing_incident
    
    # Create incident
    incident = Incident(
        title=incident_data.title,
        description=incident_data.description,
        status=incident_data.status,
        priority=incident_data.priority,
        assigned_to=incident_data.assigned_to,
        tags=incident_data.tags,
        incident_metadata=incident_data.incident_metadata,
        idempotency_key=incident_data.idempotency_key,
        team_id=team_id,
        org_id=current_user.org_id,
        organization_id=current_user.org_id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    
    # Set started_at if status is not OPEN
    if incident_data.status.value != "open":
        incident.started_at = datetime.utcnow()
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    logger.info(
        "Incident created",
        incident_id=incident.id,
        title=incident.title,
        status=incident.status.value,
        team_id=team_id,
        created_by=current_user.id
    )
    
    return incident


@router.get("/teams/{team_id}/incidents", response_model=PaginatedResponse)
async def list_incidents(
    team_id: uuid.UUID,
    params: IncidentListParams = Depends(),
    current_user: User = Depends(require_team_role(team_id, {"viewer", "editor", "admin"})),
    db: Session = Depends(get_db)
):
    """List incidents for a team with filters and pagination."""
    
    query = db.query(Incident).filter(Incident.team_id == team_id)
    
    # Apply filters
    if params.status:
        query = query.filter(Incident.status == params.status)
    
    if params.priority:
        query = query.filter(Incident.priority == params.priority)
    
    if params.since:
        query = query.filter(Incident.created_at >= params.since)
    
    if params.q:
        # Search in title and description
        search_term = f"%{params.q}%"
        query = query.filter(
            or_(
                Incident.title.ilike(search_term),
                Incident.description.ilike(search_term)
            )
        )
    
    # Apply cursor pagination
    if params.cursor:
        try:
            cursor_id = uuid.UUID(params.cursor)
            query = query.filter(Incident.id > cursor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format"
            )
    
    # Get incidents
    incidents = query.order_by(Incident.created_at.desc()).limit(params.limit + 1).all()
    
    # Check if there are more results
    has_more = len(incidents) > params.limit
    if has_more:
        incidents = incidents[:-1]
    
    # Get next cursor
    next_cursor = str(incidents[-1].id) if incidents and has_more else None
    
    return PaginatedResponse(
        items=incidents,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get incident by ID."""
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Check if user belongs to the team
    if current_user.team_id != incident.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    return incident


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    incident_data: IncidentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update incident (editor/admin only)."""
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Check if user belongs to the team and has write permissions
    if current_user.team_id != incident.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    if current_user.role.value not in {"editor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update incident"
        )
    
    # Update fields
    update_data = incident_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)
    
    # Update timestamps based on status changes
    if incident_data.status:
        if incident_data.status.value == "in_progress" and not incident.started_at:
            incident.started_at = datetime.utcnow()
        elif incident_data.status.value == "resolved" and not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()
            # Calculate resolution time
            if incident.started_at:
                incident.resolution_time_minutes = int(
                    (incident.resolved_at - incident.started_at).total_seconds() / 60
                )
        elif incident_data.status.value == "closed" and not incident.closed_at:
            incident.closed_at = datetime.utcnow()
    
    # Calculate response time if assigned
    if incident_data.assigned_to and not incident.started_at:
        incident.started_at = datetime.utcnow()
        if incident.created_at:
            incident.response_time_minutes = int(
                (incident.started_at - incident.created_at).total_seconds() / 60
            )
    
    incident.updated_by = current_user.id
    db.commit()
    db.refresh(incident)
    
    logger.info(
        "Incident updated",
        incident_id=incident.id,
        status=incident.status.value,
        updated_by=current_user.id
    )
    
    return incident


@router.delete("/incidents/{incident_id}")
async def delete_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete incident (admin only)."""
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Check if user belongs to the team and has admin permissions
    if current_user.team_id != incident.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete incident"
        )
    
    db.delete(incident)
    db.commit()
    
    logger.info(
        "Incident deleted",
        incident_id=incident.id,
        deleted_by=current_user.id
    )
    
    return {"message": "Incident deleted successfully"}
