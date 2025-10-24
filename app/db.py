"""Database configuration and session management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import structlog
from .cert_manager import cert_manager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .settings import settings

logger = structlog.get_logger(__name__)


def _build_database_url_with_certs() -> str:
    """Build database URL with SSL certificates if available."""
    parsed = urlparse(settings.postgres_dsn)
    query_params = parse_qs(parsed.query)

    # Check if sslmode is already set in the DSN (e.g., sslmode=disable)
    existing_sslmode = query_params.get('sslmode', [None])[0]

    # If sslmode is explicitly set to disable, don't add SSL config
    if existing_sslmode == 'disable':
        return settings.postgres_dsn

    # Check if SSL parameters are already present in the DSN
    ssl_params_present = any(param in query_params for param in ['sslcert', 'sslkey', 'sslrootcert'])

    # If SSL parameters are already present, don't override them
    if ssl_params_present:
        return settings.postgres_dsn

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


def _create_engine():
    """Create SQLAlchemy engine with certificate support."""
    # Build database URL with certificate support
    database_url = _build_database_url_with_certs()
    # Ensure we use psycopg driver by using postgresql+psycopg:// scheme
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Extract SSL parameters from DSN for connect_args
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    connect_args = {"options": "-c timezone=UTC"}

    # Add SSL parameters to connect_args
    for ssl_param in ['sslcert', 'sslkey', 'sslrootcert', 'sslmode']:
        if ssl_param in query_params:
            connect_args[ssl_param] = query_params[ssl_param][0]

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug,
        connect_args=connect_args,
    )

# Create SQLAlchemy engine
engine = _create_engine()

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
