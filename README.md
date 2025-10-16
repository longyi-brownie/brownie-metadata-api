# Brownie Metadata API

Enterprise-ready FastAPI service for incident management metadata. This service provides a comprehensive API for managing organizations, teams, users, agent configurations, incidents, and statistics with role-based access control and multi-tenancy support.

## Features

- **Multi-tenant Architecture**: Organization-scoped data with proper isolation
- **Role-Based Access Control (RBAC)**: Team-scoped permissions (admin, editor, viewer)
- **JWT Authentication**: Secure token-based authentication with bcrypt password hashing
- **Comprehensive CRUD APIs**: Full create, read, update, delete operations for all entities
- **Optimistic Concurrency Control**: Version-based locking for data consistency
- **Idempotency Support**: Prevent duplicate operations with idempotency keys
- **Audit Logging**: Track all mutations with user attribution
- **Soft Delete**: Safe deletion with audit trails
- **Cursor Pagination**: Efficient pagination for large datasets
- **Prometheus Metrics**: Built-in monitoring and observability
- **Structured Logging**: JSON-formatted logs with context
- **Database Migrations**: Alembic-based schema management
- **Comprehensive Testing**: Unit and integration tests with 70%+ coverage
- **Docker Support**: Containerized deployment with health checks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Organizations │    │      Teams      │    │      Users      │
│                 │◄───┤                 │◄───┤                 │
│ - Multi-tenant  │    │ - RBAC scoped   │    │ - JWT auth      │
│ - Config mgmt   │    │ - Permissions   │    │ - Role-based    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Incidents     │    │ Agent Configs   │    │     Stats       │
│                 │    │                 │    │                 │
│ - Status mgmt   │    │ - Versioned     │    │ - Time series   │
│ - Assignment    │    │ - Optimistic    │    │ - Metrics       │
│ - Idempotency   │    │   locking       │    │ - Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional)
- The `brownie-metadata-database` project (for models and migrations)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/longyi-brownie/brownie-metadata-api.git
   cd brownie-metadata-api
   make install
   ```

2. **Start the database (external dependency)**:
   The Metadata API depends on the Brownie Metadata Database project. Start it first.

   - Repository: https://github.com/longyi-brownie/brownie-metadata-database

   ```bash
   # In a separate folder
   git clone https://github.com/longyi-brownie/brownie-metadata-database.git
   cd brownie-metadata-database

   # Bring up Postgres (and the stack, if desired)
   docker-compose up -d

   # Apply migrations
   python -m alembic upgrade head
   ```

   Notes:
   - When running the API in Docker, connect to the host database using host.docker.internal:
     `METADATA_POSTGRES_DSN=postgresql://brownie:brownie@host.docker.internal:5432/brownie_metadata`
   - When running the API locally (not in Docker), use `localhost` instead of `host.docker.internal`.

4. **Start the API**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

5. **Access the API**:
   - API: http://localhost:8080
   - Docs: http://localhost:8080/docs
   - Health: http://localhost:8080/health
   - Metrics: http://localhost:8080/metrics

### Docker Deployment

```bash
# Build and start all services
make docker-up

# View logs
docker-compose logs -f metadata_api

# Stop services
make docker-down
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Create user and organization
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info

### Organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations/{id}` - Get organization
- `PUT /api/v1/organizations/{id}` - Update organization
- `GET /api/v1/organizations` - List organizations

### Teams
- `POST /api/v1/organizations/{org_id}/teams` - Create team
- `GET /api/v1/organizations/{org_id}/teams` - List teams
- `GET /api/v1/teams/{id}` - Get team
- `PUT /api/v1/teams/{id}` - Update team (admin only)
- `POST /api/v1/teams/{id}/members` - Add team member (admin only)
- `PUT /api/v1/teams/{id}/members/{user_id}` - Update member role (admin only)
- `DELETE /api/v1/teams/{id}/members/{user_id}` - Remove member (admin only)

### Users
- `POST /api/v1/organizations/{org_id}/users` - Create user
- `GET /api/v1/organizations/{org_id}/users` - List users (paginated)
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (admin only)

### Incidents
- `POST /api/v1/teams/{team_id}/incidents` - Create incident (editor/admin)
- `GET /api/v1/teams/{team_id}/incidents` - List incidents (with filters)
- `GET /api/v1/incidents/{id}` - Get incident
- `PUT /api/v1/incidents/{id}` - Update incident (editor/admin)
- `DELETE /api/v1/incidents/{id}` - Delete incident (admin only)

### Agent Configurations
- `POST /api/v1/teams/{team_id}/agent-configs` - Create config (editor/admin)
- `GET /api/v1/teams/{team_id}/agent-configs` - List configs (paginated)
- `GET /api/v1/agent-configs/{id}` - Get config
- `PUT /api/v1/agent-configs/{id}` - Update config (with optimistic locking)
- `DELETE /api/v1/agent-configs/{id}` - Delete config (admin only)

### Statistics
- `POST /api/v1/teams/{team_id}/stats` - Create stats (editor/admin)
- `GET /api/v1/teams/{team_id}/stats` - List stats (with filters)
- `GET /api/v1/organizations/{org_id}/stats` - List org stats
- `GET /api/v1/stats/{id}` - Get stats
- `DELETE /api/v1/stats/{id}` - Delete stats (admin only)

## Configuration

Environment variables (prefix: `METADATA_`):

```bash
# Database
METADATA_POSTGRES_DSN=postgresql://user:pass@host:port/db

# JWT Authentication
METADATA_JWT_SECRET=your-secret-key
METADATA_JWT_EXPIRES_MINUTES=60

# Application
METADATA_DEBUG=false
METADATA_LOG_LEVEL=INFO
METADATA_HOST=0.0.0.0
METADATA_PORT=8080

# CORS
METADATA_CORS_ORIGINS=["http://localhost:3000"]
```

## Database Schema

The service uses PostgreSQL with the following main entities:

- **Organizations**: Multi-tenant root entities
- **Teams**: Organization-scoped teams with RBAC
- **Users**: Team members with roles and authentication
- **Incidents**: Incident tracking with status and priority
- **Agent Configs**: Versioned agent configurations
- **Stats**: Time-series metrics and analytics

All entities include:
- UUID primary keys
- Created/updated timestamps
- Organization-scoped multi-tenancy
- Audit logging (created_by, updated_by)
- Soft delete support (where applicable)
- Optimistic concurrency control (where applicable)

## Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Development

```bash
# Install development dependencies
make dev

# Format code
make format

# Run linters
make lint

# Clean up
make clean
```

## Monitoring

The service includes built-in monitoring:

- **Health Check**: `/health` endpoint
- **Metrics**: `/metrics` endpoint (Prometheus format)
- **Structured Logging**: JSON logs with context
- **Request Tracing**: Request/response logging

## Security

- JWT-based authentication with configurable expiration
- bcrypt password hashing
- Role-based access control
- Multi-tenant data isolation
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy ORM
- CORS configuration

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
