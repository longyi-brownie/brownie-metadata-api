"""Statistics and metrics endpoints."""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Stats, Team, User
from ..schemas import PaginatedResponse, PaginationSchema, StatsCreate, StatsResponse

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/teams/{team_id}/stats", response_model=StatsResponse)
async def create_stats(
    team_id: uuid.UUID,
    stats_data: StatsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new statistics/metrics (editor/admin only)."""

    # Verify team exists
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

    # Check role permissions (editor/admin only)
    if current_user.role.value not in {"editor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Editor or admin role required."
        )

    # Create stats
    stats = Stats(
        metric_name=stats_data.metric_name,
        metric_type=stats_data.metric_type,
        value=stats_data.value,
        count=stats_data.count,
        timestamp=stats_data.timestamp,
        time_window=stats_data.time_window,
        labels=stats_data.labels,
        description=stats_data.description,
        unit=stats_data.unit,
        team_id=team_id,
        org_id=current_user.org_id,
        organization_id=current_user.org_id,
    )

    db.add(stats)
    db.commit()
    db.refresh(stats)

    logger.info(
        "Stats created",
        stats_id=stats.id,
        metric_name=stats.metric_name,
        team_id=team_id,
        created_by=current_user.id
    )

    return stats


@router.get("/teams/{team_id}/stats", response_model=PaginatedResponse)
async def list_stats(
    team_id: uuid.UUID,
    pagination: PaginationSchema = Depends(),
    metric_name: str | None = None,
    metric_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List statistics for a team with filters and pagination (viewer/editor/admin)."""

    # Check team membership
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )

    query = db.query(Stats).filter(Stats.team_id == team_id)

    # Apply filters
    if metric_name:
        query = query.filter(Stats.metric_name == metric_name)

    if metric_type:
        query = query.filter(Stats.metric_type == metric_type)

    if since:
        query = query.filter(Stats.timestamp >= since)

    if until:
        query = query.filter(Stats.timestamp <= until)

    # Apply cursor pagination
    if pagination.cursor:
        try:
            cursor_id = uuid.UUID(pagination.cursor)
            query = query.filter(Stats.id > cursor_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format"
            ) from e

    # Get stats
    stats_list = query.order_by(Stats.timestamp.desc()).limit(pagination.limit + 1).all()

    # Check if there are more results
    has_more = len(stats_list) > pagination.limit
    if has_more:
        stats_list = stats_list[:-1]

    # Get next cursor
    next_cursor = str(stats_list[-1].id) if stats_list and has_more else None

    return PaginatedResponse(
        items=stats_list,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/stats/{stats_id}", response_model=StatsResponse)
async def get_stats(
    stats_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics by ID."""

    stats = db.query(Stats).filter(Stats.id == stats_id).first()
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statistics not found"
        )

    # Check team membership
    if stats.team_id and current_user.team_id != stats.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )

    if current_user.org_id != stats.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this organization"
        )

    return stats


@router.get("/organizations/{org_id}/stats", response_model=PaginatedResponse)
async def list_org_stats(
    org_id: uuid.UUID,
    pagination: PaginationSchema = Depends(),
    metric_name: str | None = None,
    metric_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List statistics for an organization with filters and pagination."""

    # Check if user belongs to the organization
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this organization"
        )

    query = db.query(Stats).filter(Stats.org_id == org_id)

    # Apply filters
    if metric_name:
        query = query.filter(Stats.metric_name == metric_name)

    if metric_type:
        query = query.filter(Stats.metric_type == metric_type)

    if since:
        query = query.filter(Stats.timestamp >= since)

    if until:
        query = query.filter(Stats.timestamp <= until)

    # Apply cursor pagination
    if pagination.cursor:
        try:
            cursor_id = uuid.UUID(pagination.cursor)
            query = query.filter(Stats.id > cursor_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format"
            ) from e

    # Get stats
    stats_list = query.order_by(Stats.timestamp.desc()).limit(pagination.limit + 1).all()

    # Check if there are more results
    has_more = len(stats_list) > pagination.limit
    if has_more:
        stats_list = stats_list[:-1]

    # Get next cursor
    next_cursor = str(stats_list[-1].id) if stats_list and has_more else None

    return PaginatedResponse(
        items=stats_list,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.delete("/stats/{stats_id}")
async def delete_stats(
    stats_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete statistics (admin only)."""

    stats = db.query(Stats).filter(Stats.id == stats_id).first()
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statistics not found"
        )

    # Check organization membership
    if current_user.org_id != stats.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Check team membership
    if stats.team_id and current_user.team_id != stats.team_id:
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

    db.delete(stats)
    db.commit()

    logger.info(
        "Stats deleted",
        stats_id=stats.id,
        deleted_by=current_user.id
    )

    return {"message": "Statistics deleted successfully"}
