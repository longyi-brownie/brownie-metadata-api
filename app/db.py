"""Database configuration and session management."""

import os
import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .settings import settings
from certificates import cert_manager

logger = structlog.get_logger(__name__)


def _build_database_url_with_certs() -> str:
    """Build database URL with SSL certificates if available."""
    parsed = urlparse(settings.postgres_dsn)
    query_params = parse_qs(parsed.query)
    
    # Check if mTLS is enabled (production mode)
    mtls_enabled = os.getenv("METADATA_MTLS_ENABLED", "false").lower() == "true"
    
    # Get SSL configuration from certificate manager
    ssl_config = cert_manager.get_database_ssl_config(mtls_enabled=mtls_enabled)
    
    # Add SSL parameters to query string
    for key, value in ssl_config.items():
        if value:
            query_params[key] = [str(value)]
    
    # Rebuild query string
    new_query = urlencode(query_params, doseq=True)
    
    # Rebuild URL
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


# Create SQLAlchemy engine with certificate support
database_url = _build_database_url_with_certs()
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug,
    # Use UTC timezone
    connect_args={"options": "-c timezone=UTC"},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[Session, None]:
    """Async context manager for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database connection and verify connectivity."""
    try:
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            
            # Set timezone to UTC
            conn.execute(text("SET timezone = 'UTC'"))
            conn.commit()
            
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(
            "Failed to connect to database",
            error=str(e),
            hint=(
                "Ensure the database is running. If using local docker, start the DB from the"
                " brownie-metadata-database repo (docker-compose up -d) and set METADATA_POSTGRES_DSN"
                " to point at host.docker.internal:5432 when running API in Docker."
            ),
        )
        # Fail fast so container exits and orchestration can restart it once DB is up
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))