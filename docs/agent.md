# AI Agent Guidelines for Brownie Metadata API

## Project Context
This is an **enterprise-grade FastAPI application** for metadata management that will be **sold to customers**. The codebase must maintain the highest standards of security, reliability, and maintainability.

## Core Architecture

### Technology Stack
- **FastAPI** with async/await patterns
- **SQLAlchemy ORM** with PostgreSQL
- **JWT authentication** with Argon2 password hashing
- **Multi-tenant architecture** (organization-scoped data)
- **Role-based access control** (team-scoped permissions)
- **Certificate-based database authentication** (no passwords)
- **Prometheus metrics** and structured logging

### Security Model
- **Data Isolation**: All data is scoped to organizations
- **Authentication**: JWT tokens with secure secrets
- **Authorization**: Team-based roles (admin, member, viewer)
- **Database Security**: mTLS with certificates only
- **Password Security**: Argon2 hashing (industry standard)

## Development Guidelines

### When Making Changes

1. **Security First**: Every change must consider security implications
2. **Multi-Tenancy**: Ensure data isolation is maintained
3. **Authentication**: Verify JWT token validation on all protected endpoints
4. **Input Validation**: Use Pydantic models for all request/response validation
5. **Error Handling**: Implement comprehensive error handling with proper HTTP status codes
6. **Logging**: Add structured logging for audit trails
7. **Testing**: Include tests for all new functionality
8. **Code Quality**: Run linting tools before committing code

### Code Quality Tools (MANDATORY BEFORE COMMIT)

**Always run these tools before committing any code:**

```bash
# 1. Lint and auto-fix code issues
uv run ruff check . --fix

# 2. Format code
uv run ruff format .

# 3. Type checking
uv run mypy app/

# 4. Security linting
uv run bandit -r app/

# 5. Dependency vulnerability check
uv run safety check
```

**Tools Overview:**
- **Ruff**: Fast Python linter and formatter (replaces black, isort, flake8)
- **MyPy**: Static type checking for type safety
- **Bandit**: Security linting to catch common security issues
- **Safety**: Dependency vulnerability scanning

**Why This Matters:**
- **Enterprise Quality**: Customers expect high-quality, secure code
- **CI/CD Pipeline**: GitHub Actions will fail if linting errors exist
- **Security**: Bandit catches common security vulnerabilities
- **Maintainability**: Clean, consistent code is easier to maintain
- **Type Safety**: MyPy prevents runtime type errors

### Code Patterns

#### Authentication Flow
```python
@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify organization access
    if current_user.org_id != target_org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # Implementation
```

#### Database Operations
```python
async def create_entity(entity_data: EntityCreate, db: Session) -> Entity:
    entity = Entity(
        org_id=entity_data.org_id,  # Always include org_id for multi-tenancy
        # ... other fields
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity
```

#### Error Handling
```python
try:
    result = await some_operation()
except SpecificException as e:
    logger.error("Operation failed", extra={"error": str(e), "user_id": current_user.id})
    raise HTTPException(status_code=400, detail="Operation failed")
```

### File Organization
- `app/main.py`: FastAPI app initialization
- `app/settings.py`: Configuration management
- `app/db.py`: Database connection and session management
- `app/auth.py`: Authentication and authorization
- `app/models.py`: SQLAlchemy model imports (from brownie-metadata-db package)
- `app/schemas.py`: Pydantic request/response models
- `app/routers/`: API endpoint routers organized by domain

### Database Considerations
- **Multi-Tenancy**: All queries must include organization scoping
- **Soft Deletes**: Use `deleted_at` timestamps instead of hard deletes
- **Audit Fields**: Include `created_at`, `updated_at`, `created_by`, `updated_by`
- **UUIDs**: Use UUIDs for all primary keys
- **Transactions**: Use database transactions for multi-step operations

### Security Requirements
- **Input Validation**: Validate all input with Pydantic models
- **SQL Injection**: Use SQLAlchemy ORM (never raw SQL)
- **Authentication**: Verify JWT tokens on all protected endpoints
- **Authorization**: Check organization and team permissions
- **Logging**: Log all authentication and authorization events
- **Secrets**: Never hardcode secrets, use environment variables

### Performance Considerations
- **Async Operations**: Use async/await for I/O operations
- **Database Indexes**: Ensure proper indexing for queries
- **Pagination**: Implement pagination for list endpoints
- **Connection Pooling**: Use database connection pooling
- **Caching**: Consider Redis for frequently accessed data

### Testing Requirements
- **Unit Tests**: Test all business logic
- **Integration Tests**: Test API endpoints with database
- **Authentication Tests**: Test JWT token validation
- **Authorization Tests**: Test role-based access control
- **Error Handling Tests**: Test error scenarios
- **Performance Tests**: Test critical paths

### Monitoring & Observability
- **Metrics**: Add Prometheus metrics for all endpoints
- **Logging**: Use structured logging with correlation IDs
- **Health Checks**: Implement health checks for dependencies
- **Error Tracking**: Monitor and alert on error rates

## Common Tasks

### Adding a New Endpoint
1. Create Pydantic schemas for request/response validation
2. Add authentication dependencies (`get_current_user`, `require_org_access`)
3. Implement proper error handling with `HTTPException`
4. Add comprehensive docstrings
5. Include in appropriate router
6. Add tests for all scenarios

### Adding a New Model
1. Update the database package (brownie-metadata-db)
2. Create Alembic migration
3. Update Pydantic schemas
4. Add proper indexes
5. Test with sample data

### Database Changes
1. Create Alembic migration for schema changes
2. Update Pydantic schemas to match new fields
3. Add proper indexes for performance
4. Consider backward compatibility
5. Test migration on sample data

## Anti-Patterns to Avoid

### Security Anti-Patterns
- ❌ Don't use raw SQL queries
- ❌ Don't store passwords in plain text
- ❌ Don't expose internal database errors
- ❌ Don't skip input validation
- ❌ Don't hardcode secrets
- ❌ Don't ignore security headers

### Architecture Anti-Patterns
- ❌ Don't use synchronous operations for I/O
- ❌ Don't skip error handling
- ❌ Don't ignore multi-tenancy requirements
- ❌ Don't skip authentication checks
- ❌ Don't use hardcoded configuration values

### Code Quality Anti-Patterns
- ❌ Don't skip tests
- ❌ Don't ignore logging requirements
- ❌ Don't skip documentation
- ❌ Don't ignore performance implications
- ❌ Don't skip code review

## Enterprise Considerations

### Customer Requirements
- **Reliability**: 99.9% uptime target
- **Security**: Enterprise-grade security controls
- **Scalability**: Support for thousands of users
- **Compliance**: Audit trails and data governance
- **Support**: Comprehensive documentation and troubleshooting guides

### Production Readiness
- **Monitoring**: Comprehensive observability
- **Alerting**: Proactive issue detection
- **Backup**: Data backup and recovery procedures
- **Scaling**: Horizontal scaling capabilities
- **Security**: Regular security audits and updates

### Documentation Requirements
- **API Documentation**: Comprehensive OpenAPI documentation
- **Deployment Guides**: Step-by-step deployment instructions
- **Security Guides**: Security best practices and configuration
- **Troubleshooting**: Common issues and solutions
- **Integration Guides**: Client integration examples

## Code Review Checklist

When reviewing code, ensure:
- [ ] Security implications reviewed
- [ ] Multi-tenancy requirements met
- [ ] Input validation implemented
- [ ] Error handling comprehensive
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Performance impact considered
- [ ] Database migrations included if needed
- [ ] Logging and metrics added
- [ ] Backward compatibility maintained
- [ ] Authentication/authorization verified
- [ ] Audit trail implemented

## Emergency Procedures

### Security Incidents
1. Immediately revoke compromised tokens
2. Check audit logs for suspicious activity
3. Update security configurations
4. Notify security team
5. Document incident and response

### Performance Issues
1. Check database connection pool status
2. Review slow query logs
3. Monitor resource utilization
4. Scale horizontally if needed
5. Optimize problematic queries

### Data Issues
1. Check database connectivity
2. Verify certificate validity
3. Review migration status
4. Check for data corruption
5. Restore from backup if necessary

Remember: This is an enterprise product that customers will depend on for their business operations. Every change must be made with the highest standards of quality, security, and reliability.
