"""Import models from the database project."""

# Import all models from the database project
# This assumes brownie-metadata-database is installed as a dependency
try:
    from brownie_metadata_database.models import (
        Organization,
        Team,
        User,
        Incident,
        AgentConfig,
        Stats,
        Config,
        UserRole,
        IncidentStatus,
        IncidentPriority,
        AgentType,
    )
except ImportError:
    # Fallback for development when database project is not installed
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'brownie-metadata-database', 'src'))
    
    from database.models import (
        Organization,
        Team,
        User,
        Incident,
        AgentConfig,
        Stats,
        Config,
        UserRole,
        IncidentStatus,
        IncidentPriority,
        AgentType,
    )

# Re-export for convenience
__all__ = [
    "Organization",
    "Team",
    "User",
    "Incident",
    "AgentConfig",
    "Stats",
    "Config",
    "UserRole",
    "IncidentStatus",
    "IncidentPriority",
    "AgentType",
]