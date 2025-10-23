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

### Database Library Architecture

```mermaid
graph TB
    subgraph "FastAPI Server"
        A[API Endpoints]
        B[Business Logic]
        C[SQLAlchemy ORM]
        D[Certificate Manager]
    end
    
    subgraph "Database"
        E[PostgreSQL]
    end
    
    A --> B
    B --> C
    C -->|DSN + Client Cert| E
    D -->|Provides Certs| C
    
    style A fill:#e1f5fe
    style C fill:#e8f5e8
    style E fill:#f3e5f5
    style D fill:#fff2cc
```

**How It Works:**
1. **FastAPI endpoints** receive requests
2. **Business logic** processes the request
3. **SQLAlchemy ORM** queries the database using models from `brownie-metadata-database`
4. **Certificate Manager** provides client certificates for authentication
5. **PostgreSQL** authenticates using client certificate CN

**Authentication Flow:**
```python
# FastAPI Server Code Example
from sqlalchemy.orm import Session
from brownie_metadata_database.models import Organization

@app.get("/organizations/{org_id}")
async def get_organization(org_id: int, db: Session = Depends(get_db)):
    # SQLAlchemy ORM with certificate authentication
    org = db.query(Organization).filter(Organization.id == org_id).first()
    return org
```

**Database Connection:**
```python
# DSN with client certificates
DATABASE_URL = (
    f"postgresql://user@host:5432/db"
    f"?sslmode=require"
    f"&sslcert=/path/to/client.crt"
    f"&sslkey=/path/to/client.key"
    f"&sslrootcert=/path/to/ca.crt"
)
```

### Entity Relationships

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
   ```

2. **Set up environment**:
   ```bash
   cp env.template .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**:
   ```bash
   make install
   ```

4. **Start the database (external dependency)**:
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

3. **Generate development certificates** (optional):
   ```bash
   # Generate self-signed certificates for database authentication
   python scripts/generate_dev_certs.py
   
   # This creates certificates in dev-certs/ directory
   # Update your PostgreSQL config to use these certificates
   ```

5. **Start the API**:
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

6. **Access the API**:
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

### Okta OIDC
- `GET /api/v1/okta/login` - Initiate Okta OIDC login
- `GET /api/v1/okta/callback` - Handle Okta OIDC callback
- `GET /api/v1/okta/userinfo` - Get user info from Okta token

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

### Environment Setup

**⚠️ SECURITY WARNING**: Never commit secrets to version control!

1. **Copy the template**:
   ```bash
   cp env.template .env
   ```

2. **Update all secrets**:
   ```bash
   # Generate a strong JWT secret
   openssl rand -base64 32
   
   # Edit .env file with your values
   nano .env
   ```

3. **Validate configuration**:
   ```bash
   # The app validates secrets on startup
   uvicorn app.main:app --reload
   ```

### Environment Variables

**Required for all environments:**
```bash
# Database
METADATA_POSTGRES_DSN=postgresql://user:pass@host:port/db

# JWT Authentication (MUST be changed from default!)
METADATA_JWT_SECRET=your-strong-secret-here  # Generate with: openssl rand -base64 32
METADATA_JWT_EXPIRES_MINUTES=60

# Application
METADATA_DEBUG=false
METADATA_LOG_LEVEL=INFO
METADATA_HOST=0.0.0.0
METADATA_PORT=8080

# CORS (restrict in production)
METADATA_CORS_ORIGINS=["http://localhost:3000"]
```

**Production only:**
```bash
# Certificate Management (Production)
VAULT_ENABLED=true
VAULT_URL=https://vault.yourcompany.com
VAULT_TOKEN=your-vault-token
VAULT_CERT_PATH=secret/brownie-metadata/certs

# mTLS Configuration
METADATA_MTLS_ENABLED=true
```

**Development only:**
```bash
# Certificate Management (Development)
LOCAL_CERT_DIR=dev-certs
```

### Security Configuration

See [SECURITY.md](SECURITY.md) for detailed security requirements and best practices.

### Authentication & Authorization

**Multi-Auth Support:**
- **JWT Authentication** - Email/password with bcrypt hashing
- **Okta OIDC** - Enterprise SSO integration
- **Role-Based Access Control (RBAC)** - Team-scoped permissions
- **Permission System** - Granular access control

**Authentication Flow:**
```mermaid
graph TB
    A[Client Request] --> B{Auth Method}
    B -->|JWT| C[Verify JWT Token]
    B -->|Okta| D[OIDC Flow]
    C --> E[Check User Permissions]
    D --> F[Exchange Code for Token]
    F --> G[Get User Info]
    G --> H[Create/Update User]
    H --> E
    E --> I[Authorize Request]
    I --> J[Execute Operation]
    
    style A fill:#e1f5fe
    style E fill:#e8f5e8
    style I fill:#fff2cc
```

**RBAC Permissions:**
- **Admin**: Full access to all resources
- **Editor**: Read/write access to incidents, configs, stats
- **Viewer**: Read-only access to all resources

### Security Features

**Database Security:**
- **Client Certificate Authentication** - No passwords, uses certificate CN
- **mTLS Support** - Production mutual certificate verification
- **Encrypted Connections** - All data encrypted in transit
- **Certificate Management** - Vault PKI (production) or local files (development)
- **PostgreSQL Verification** - Server validates client certificate

**API Security:**
- **JWT Token Validation** - Secure token-based authentication
- **Okta OIDC Integration** - Enterprise SSO support
- **Role-Based Permissions** - Granular access control
- **Multi-tenant Isolation** - Organization-scoped data access
- **Input Validation** - Pydantic schema validation
- **SQL Injection Prevention** - SQLAlchemy ORM protection

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
