"""Agent configuration management endpoints."""

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_team_role
from ..db import get_db
from ..models import AgentConfig, Team
from ..schemas import (
    AgentConfigCreate, AgentConfigResponse, AgentConfigUpdate, 
    AgentConfigListParams, PaginatedResponse
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/teams/{team_id}/agent-configs", response_model=AgentConfigResponse)
async def create_agent_config(
    team_id: uuid.UUID,
    config_data: AgentConfigCreate,
    current_user: User = Depends(require_team_role(team_id, {"editor", "admin"})),
    db: Session = Depends(get_db)
):
    """Create a new agent configuration (editor/admin only)."""
    
    # Verify team exists
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Check for unique name within team
    existing_config = db.query(AgentConfig).filter(
        AgentConfig.team_id == team_id,
        AgentConfig.name == config_data.name
    ).first()
    
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent configuration with this name already exists in team"
        )
    
    # Create agent config
    agent_config = AgentConfig(
        name=config_data.name,
        description=config_data.description,
        agent_type=config_data.agent_type,
        is_active=config_data.is_active,
        config=config_data.config,
        execution_timeout_seconds=config_data.execution_timeout_seconds,
        max_retries=config_data.max_retries,
        retry_delay_seconds=config_data.retry_delay_seconds,
        triggers=config_data.triggers,
        conditions=config_data.conditions,
        tags=config_data.tags,
        config_metadata=config_data.config_metadata,
        team_id=team_id,
        org_id=current_user.org_id,
        organization_id=current_user.org_id,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    
    db.add(agent_config)
    db.commit()
    db.refresh(agent_config)
    
    logger.info(
        "Agent config created",
        config_id=agent_config.id,
        name=agent_config.name,
        team_id=team_id,
        created_by=current_user.id
    )
    
    return agent_config


@router.get("/teams/{team_id}/agent-configs", response_model=PaginatedResponse)
async def list_agent_configs(
    team_id: uuid.UUID,
    params: AgentConfigListParams = Depends(),
    current_user: User = Depends(require_team_role(team_id, {"viewer", "editor", "admin"})),
    db: Session = Depends(get_db)
):
    """List agent configurations for a team with pagination."""
    
    query = db.query(AgentConfig).filter(AgentConfig.team_id == team_id)
    
    # Apply filters
    if params.agent_type:
        query = query.filter(AgentConfig.agent_type == params.agent_type)
    
    if params.is_active is not None:
        query = query.filter(AgentConfig.is_active == params.is_active)
    
    # Apply cursor pagination
    if params.cursor:
        try:
            cursor_id = uuid.UUID(params.cursor)
            query = query.filter(AgentConfig.id > cursor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor format"
            )
    
    # Get configs
    configs = query.order_by(AgentConfig.id).limit(params.limit + 1).all()
    
    # Check if there are more results
    has_more = len(configs) > params.limit
    if has_more:
        configs = configs[:-1]
    
    # Get next cursor
    next_cursor = str(configs[-1].id) if configs and has_more else None
    
    return PaginatedResponse(
        items=configs,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/agent-configs/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent configuration by ID."""
    
    config = db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check if user belongs to the team
    if current_user.team_id != config.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    return config


@router.put("/agent-configs/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: uuid.UUID,
    config_data: AgentConfigUpdate,
    if_match: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update agent configuration with optimistic locking (editor/admin only)."""
    
    config = db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check if user belongs to the team and has write permissions
    if current_user.team_id != config.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    if current_user.role.value not in {"editor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update agent configuration"
        )
    
    # Check optimistic locking
    if if_match and if_match != str(config.version):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configuration was modified by another user. Please refresh and try again."
        )
    
    # Check for unique name within team (if name is being updated)
    if config_data.name and config_data.name != config.name:
        existing_config = db.query(AgentConfig).filter(
            AgentConfig.team_id == config.team_id,
            AgentConfig.name == config_data.name,
            AgentConfig.id != config_id
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent configuration with this name already exists in team"
            )
    
    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    # Increment version for optimistic locking
    config.version += 1
    config.updated_by = current_user.id
    
    db.commit()
    db.refresh(config)
    
    logger.info(
        "Agent config updated",
        config_id=config.id,
        version=config.version,
        updated_by=current_user.id
    )
    
    return config


@router.delete("/agent-configs/{config_id}")
async def delete_agent_config(
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete agent configuration (admin only)."""
    
    config = db.query(AgentConfig).filter(AgentConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check if user belongs to the team and has admin permissions
    if current_user.team_id != config.team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this team"
        )
    
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete agent configuration"
        )
    
    # Soft delete by setting is_active to False
    config.is_active = False
    config.updated_by = current_user.id
    
    db.commit()
    
    logger.info(
        "Agent config deleted",
        config_id=config.id,
        deleted_by=current_user.id
    )
    
    return {"message": "Agent configuration deleted successfully"}
