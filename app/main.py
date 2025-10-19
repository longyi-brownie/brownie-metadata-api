"""Main FastAPI application."""

import structlog
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .auth import router as auth_router
from .okta_auth import okta_router
from .db import init_db, close_db
from .routers import (
    organizations,
    teams,
    users,
    agent_configs,
    incidents,
    stats,
)
from .schemas import HealthResponse
from .settings import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Brownie Metadata API", version="0.1.0")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Brownie Metadata API")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="Brownie Metadata API",
    description="Enterprise-ready FastAPI service for incident management metadata",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware for collecting metrics and logging."""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Log request
    logger.info(
        "HTTP request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
        client_ip=request.client.host if request.client else None,
    )
    
    return response


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        from .db import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",
        database=db_status,
    )


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Mount routers under /api/v1
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(okta_router, prefix="/api/v1", tags=["okta"])
app.include_router(organizations.router, prefix="/api/v1", tags=["organizations"])
app.include_router(teams.router, prefix="/api/v1", tags=["teams"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(agent_configs.router, prefix="/api/v1", tags=["agent-configs"])
app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
