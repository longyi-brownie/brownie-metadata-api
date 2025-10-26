# Brownie Metadata API

> **Enterprise-grade metadata management API with JWT authentication, multi-tenancy, and role-based access control**

[![CI/CD](https://github.com/longyi-brownie/brownie-metadata-api/workflows/CI%2FCD/badge.svg)](https://github.com/longyi-brownie/brownie-metadata-api/actions)
[![Security](https://img.shields.io/badge/security-enterprise--grade-green.svg)](./SECURITY.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## 🎯 **Overview**

Brownie Metadata API is a production-ready FastAPI service that provides secure, scalable metadata management for enterprise applications. Built with security-first principles, it offers JWT authentication, multi-tenant architecture, and comprehensive audit logging.

### ✨ **Key Features**

- **🔐 Enterprise Security**: JWT authentication with Argon2 password hashing
- **🏢 Multi-Tenancy**: Organization-scoped data isolation
- **👥 Role-Based Access Control**: Team-scoped permissions (admin, member, viewer)
- **📊 Observability**: Prometheus metrics, structured logging, health checks
- **🔒 Certificate Authentication**: mTLS database connections
- **📈 Scalable**: Stateless design for horizontal scaling
- **🛡️ Production Ready**: Comprehensive error handling and validation

## 🚀 **Quick Start**

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ with SSL support
- Docker & Docker Compose (for development)

### Installation

   ```bash
# Clone the repository
git clone https://github.com/longyi-brownie/brownie-metadata-api.git
   cd brownie-metadata-api

# Install dependencies
uv install

# Set up environment
cp config/env.template .env
   # Edit .env with your configuration

### Code Quality Tools

**Before committing code, always run:**

```bash
# Lint and auto-fix
uv run ruff check . --fix

# Format code
uv run ruff format .

# Type checking
uv run mypy app/

# Security checks
uv run bandit -r app/
uv run safety check
```

### Development Setup

   ```bash
# Start the database (from brownie-metadata-database repo)
cd ../brownie-metadata-database
   docker-compose up -d

# Start the API server
cd ../brownie-metadata-api
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## 🔐 **Authentication Guide**

### For API Clients

The API uses JWT (JSON Web Token) authentication. Here's how to integrate:

#### 1. **User Registration**

   ```bash
curl -X POST http://localhost:8080/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "securepassword123",
    "username": "johndoe",
    "full_name": "John Doe",
    "organization_name": "Acme Corp",
    "team_name": "Engineering"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2. **User Login**

   ```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "securepassword123"
  }'
```

#### 3. **Making Authenticated Requests**

```bash
curl -X GET http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 4. **Client Integration Examples**

**Python:**
```python
import requests

# Login
response = requests.post('http://localhost:8080/api/v1/auth/login', json={
    'email': 'user@company.com',
    'password': 'securepassword123'
})
token = response.json()['access_token']

# Make authenticated requests
headers = {'Authorization': f'Bearer {token}'}
user_info = requests.get('http://localhost:8080/api/v1/auth/me', headers=headers)
```

**JavaScript:**
```javascript
// Login
const loginResponse = await fetch('http://localhost:8080/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'securepassword123'
  })
});
const { access_token } = await loginResponse.json();

// Make authenticated requests
const userResponse = await fetch('http://localhost:8080/api/v1/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### Token Management

- **Expiration**: Tokens expire after 1 hour (3600 seconds)
- **Refresh**: Use the login endpoint to get a new token
- **Storage**: Store tokens securely (httpOnly cookies recommended for web apps)
- **Security**: Never expose tokens in client-side code or logs

## 📚 **API Documentation**

### Interactive Documentation

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI Schema**: http://localhost:8080/openapi.json

### Core Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/auth/signup` | POST | Register new user | No |
| `/api/v1/auth/login` | POST | User login | No |
| `/api/v1/auth/me` | GET | Get current user | Yes |
| `/api/v1/users/{user_id}` | GET | Get user by ID | Yes |
| `/api/v1/organizations/{org_id}/users` | GET | List organization users | Yes |
| `/health` | GET | Health check | No |
| `/metrics` | GET | Prometheus metrics | No |

## 🏗️ **Architecture**

### Multi-Tenant Design

```
Organization (Acme Corp)
├── Team (Engineering)
│   ├── User (admin) - Full access
│   ├── User (member) - Read/Write
│   └── User (viewer) - Read only
└── Team (Marketing)
    ├── User (admin) - Full access
    └── User (member) - Read/Write
```

### Security Model

- **Data Isolation**: All data is scoped to organizations
- **Role-Based Access**: Team-scoped permissions
- **Certificate Authentication**: Database uses mTLS
- **Password Security**: Argon2 hashing (industry standard)

## 📁 **Project Structure**

```
brownie-metadata-api/
├── app/                           # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── settings.py               # Configuration management
│   ├── db.py                    # Database connection
│   ├── auth.py                  # Authentication logic
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   └── routers/                 # API endpoints
├── tests/                        # Test suite
│   ├── integration/             # Integration tests
│   ├── test_auth_comprehensive.py
│   └── test_user_crud_comprehensive.py
├── docs/                         # Documentation
│   ├── api/                     # API documentation
│   ├── security/                # Security guides
│   ├── operations/              # Operations runbooks
│   └── development/             # Development guides
├── config/                       # Configuration templates
│   ├── env.example              # Environment example
│   └── env.template             # Environment template
├── scripts/                      # Utility scripts
│   ├── security/                # Security scripts
│   ├── deployment/              # Deployment scripts
│   └── monitoring/              # Monitoring scripts
├── infrastructure/               # Infrastructure as Code
│   ├── docker/                  # Docker configurations
│   ├── kubernetes/              # Kubernetes manifests
│   └── terraform/               # Terraform configurations
├── security/                     # Security configurations
│   └── certificates/            # Certificate management
├── monitoring/                   # Monitoring configurations
│   ├── prometheus/              # Prometheus configs
│   ├── grafana/                 # Grafana dashboards
│   └── alerts/                  # Alert rules
└── pyproject.toml               # Project configuration
```

## 🔧 **Configuration**

### Environment Variables

Copy the configuration template and customize for your environment:

```bash
# Copy configuration template
cp config/env.template .env

# Edit with your settings
nano .env
```

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `METADATA_POSTGRES_DSN` | Database connection string | - | Yes |
| `METADATA_JWT_SECRET` | JWT signing secret | - | Yes |
| `METADATA_HOST` | Server host | `0.0.0.0` | No |
| `METADATA_PORT` | Server port | `8080` | No |

**Configuration Files:**
- `config/env.template` - Complete configuration template with documentation
- `config/env.example` - Minimal example configuration

### Database Configuration

The API requires a PostgreSQL database with SSL support. See [Database Setup](./docs/database-setup.md) for detailed instructions.

## 📊 **Monitoring & Observability**

### Health Checks

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed health check
curl http://localhost:8080/health/detailed
```

### Metrics

Prometheus metrics are available at `/metrics`:

```bash
curl http://localhost:8080/metrics
```

Key metrics:
- `http_requests_total` - Request count by endpoint and status
- `http_request_duration_seconds` - Request latency
- `database_connections_active` - Active database connections
- `jwt_tokens_issued_total` - JWT tokens issued

### Logging

Structured JSON logging with configurable levels:

```bash
# View logs
docker logs brownie-metadata-api

# Filter by level
docker logs brownie-metadata-api 2>&1 | jq 'select(.level == "error")'
```

## 🚀 **Deployment**

### Docker Deployment

```bash
# Build image
docker build -t brownie-metadata-api .

# Run container
docker run -d \
  --name brownie-metadata-api \
  -p 8080:8080 \
  -e METADATA_POSTGRES_DSN="postgresql://user:pass@db:5432/db" \
  -e METADATA_JWT_SECRET="your-secret-key" \
  brownie-metadata-api
```

### Kubernetes Deployment

See [Kubernetes Deployment Guide](./docs/kubernetes.md) for production deployment.

### Scaling

The API is stateless and can be horizontally scaled:

```bash
# Scale to 3 replicas
kubectl scale deployment brownie-metadata-api --replicas=3
```

## 🧪 **Testing**

### Setup Test Database

You have 3 options to run tests:

#### Option 1: Docker Compose (Recommended for Local Testing)

```bash
# Start test PostgreSQL container
docker-compose -f tests/docker-compose.test.yml up -d

# Run tests
export METADATA_JWT_SECRET="test-jwt-secret-key-for-testing-only"
export METADATA_POSTGRES_DSN="postgresql://postgres:postgres@localhost:5433/test_brownie_metadata?sslmode=disable"
uv run pytest tests/
```

#### Option 2: Testcontainers (Automatic, Requires Docker Desktop)

```bash
# Just run tests - testcontainers will spin up Postgres automatically
export METADATA_JWT_SECRET="test-jwt-secret-key-for-testing-only"
uv run pytest tests/
```

#### Option 3: Local PostgreSQL

```bash
# Start your local PostgreSQL
brew services start postgresql  # macOS
# or
sudo systemctl start postgresql  # Linux

# Create test database
createdb test_brownie_metadata

# Run tests
export METADATA_JWT_SECRET="test-jwt-secret-key-for-testing-only"
export METADATA_POSTGRES_DSN="postgresql://your_user@localhost:5432/test_brownie_metadata?sslmode=disable"
uv run pytest tests/
```

### Run Tests

```bash
# Unit tests
uv run pytest tests/

# Integration tests
uv run pytest tests/integration/

# All tests with coverage
uv run pytest --cov=app tests/
```

### Test Coverage

Current coverage: **85%+**

## 🔒 **Security**

For detailed security information, see [SECURITY.md](./SECURITY.md).

### Security Features

- ✅ JWT authentication with secure secrets
- ✅ Argon2 password hashing
- ✅ Certificate-based database authentication
- ✅ Input validation and sanitization
- ✅ SQL injection prevention
- ✅ CORS configuration
- ✅ Rate limiting (configurable)
- ✅ Audit logging

## 📖 **Documentation**

- **Documentation Hub**: [docs/README.md](./docs/README.md)
- **API Reference**: [docs/api/README.md](./docs/api/README.md)
- **Security Guide**: [docs/SECURITY.md](./docs/SECURITY.md)
- **Operations Guide**: [docs/operations.md](./docs/operations.md)
- **Deployment Guide**: [docs/deployment.md](./docs/deployment.md)
- **Development Guide**: [docs/DEVELOPER_SETUP.md](./docs/DEVELOPER_SETUP.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Contributing](./CONTRIBUTING.md)

## 🤝 **Support**

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/longyi-brownie/brownie-metadata-api/issues)
- **Enterprise Support**: info@brownie-ai.com

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

**Built with ❤️ for enterprise applications**