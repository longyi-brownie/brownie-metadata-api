# Changelog

All notable changes to the Brownie Metadata API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-27

### Initial Release

#### Core Features
- **FastAPI Application** - Modern async Python web framework
- **JWT Authentication** - Secure token-based auth with Argon2 password hashing
- **Multi-Tenant Architecture** - Organization and team-based data isolation
- **Role-Based Access Control** - Admin, member, and viewer roles
- **PostgreSQL with SSL** - Production-ready database with TLS encryption
- **RESTful API** - Complete CRUD operations for all resources

#### API Endpoints
- **Authentication** - `/api/v1/auth/` (signup, login, current user)
- **Users** - `/api/v1/users/` (CRUD operations)
- **Organizations** - `/api/v1/organizations/` (CRUD operations)
- **Teams** - `/api/v1/teams/` (CRUD operations, member management)
- **Incidents** - `/api/v1/incidents/` (CRUD operations, filtering, pagination)
- **Agent Configs** - `/api/v1/agent-configs/` (CRUD operations)
- **Statistics** - `/api/v1/stats/` (metrics and analytics)

#### Security
- **SSL/TLS** - Full SSL support with verify-full mode
- **Certificate Authentication** - mTLS ready for production
- **Argon2 Password Hashing** - Industry-standard password security
- **Input Validation** - Pydantic models for all endpoints
- **Audit Logging** - Structured logging with correlation IDs
- **Security Scanning** - Bandit, Safety, and Trivy in CI

#### Testing
- **57 Tests** - Comprehensive test coverage (62%)
- **SSL Testing** - All tests run with SSL enabled
- **Integration Tests** - Full API integration testing
- **Unit Tests** - Component-level testing
- **CI/CD** - GitHub Actions with automated testing

#### Infrastructure
- **Docker Support** - Production-ready Dockerfile
- **PostgreSQL 16** - Latest stable PostgreSQL with SSL
- **Health Checks** - `/health` and `/metrics` endpoints
- **Prometheus Metrics** - Built-in observability
- **Structured Logging** - JSON logs with structlog

#### Developer Experience
- **OpenAPI Documentation** - Auto-generated API docs at `/docs`
- **Type Safety** - Full type hints with mypy
- **Code Quality** - Ruff linting and formatting
- **Pre-commit Hooks** - Automated code quality checks
- **Comprehensive Documentation** - Setup, deployment, and security guides

#### Database Schema
- **Users** - User accounts with authentication
- **Organizations** - Multi-tenant organization support
- **Teams** - Team-based access control
- **Incidents** - Incident tracking and management
- **Agent Configs** - AI agent configuration management
- **Audit Fields** - Created/updated timestamps and user tracking

### Technical Stack
- **Python 3.11+** - Modern Python with async support
- **FastAPI 0.104+** - High-performance web framework
- **SQLAlchemy 2.0+** - Modern ORM with async support
- **PostgreSQL 16** - Latest stable database
- **Pydantic 2.0+** - Data validation and serialization
- **JWT** - JSON Web Tokens for authentication
- **Argon2** - Password hashing
- **Structlog** - Structured logging
- **Prometheus** - Metrics and monitoring

### Deployment
- **Production Ready** - SSL, security, and monitoring built-in
- **Docker** - Containerized deployment
- **Kubernetes Ready** - Stateless design for horizontal scaling
- **Environment-based Config** - 12-factor app principles
- **Health Checks** - Kubernetes/load balancer integration

[0.1.0]: https://github.com/longyi-brownie/brownie-metadata-api/releases/tag/v0.1.0

