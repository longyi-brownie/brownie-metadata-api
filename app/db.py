"""Database configuration and session management."""

import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .settings import settings

logger = structlog.get_logger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.postgres_dsn,
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