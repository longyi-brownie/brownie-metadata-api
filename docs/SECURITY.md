# Security

## Authentication

### JWT Tokens

All API requests require JWT authentication tokens.

**How to get a token:**
```bash
# Sign up new user
curl -X POST http://your-api/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "securepassword",
    "username": "user",
    "full_name": "User Name",
    "organization_name": "Company Name",
    "team_name": "Engineering"
  }'

# Login
curl -X POST http://your-api/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com", "password": "securepassword"}'
```

**Token usage:**
```bash
curl -H "Authorization: Bearer <token>" http://your-api/api/v1/users/me
```

### Password Security

- Passwords hashed with **Argon2** (industry standard)
- Minimum 12 characters required
- Passwords never logged or stored in plain text

## Database Security

### Certificate Authentication (Production)

- ✅ No database passwords required
- ✅ Certificate-based authentication
- ✅ SSL/TLS encryption for all connections
- ✅ Mutual TLS (mTLS) verification

**Configuration:**
```bash
# Store certificates in Vault
VAULT_ENABLED=true
VAULT_URL=https://vault.yourcompany.com
VAULT_TOKEN=your-token

# Or use local certificate files
LOCAL_CERT_DIR=/path/to/certs
```

## API Security

- **HTTPS only** in production
- **Input validation** via Pydantic schemas
- **SQL injection prevention** via SQLAlchemy ORM
- **CORS protection** - restrict to authorized domains
- **Rate limiting** - built-in throttling
- **Audit logging** - all mutations tracked

## Security Checklist

**Before going live:**
- [ ] JWT secret changed from default (32+ chars)
- [ ] HTTPS enabled with valid certificates
- [ ] CORS origins restricted to your domains
- [ ] Debug mode disabled
- [ ] Database uses certificate authentication
- [ ] Secrets stored securely (Vault/Secrets Manager)
- [ ] Monitoring and alerting configured
- [ ] Security headers configured in load balancer

**Regular maintenance:**
- Rotate JWT secrets quarterly
- Update certificates before expiration
- Review access logs monthly
- Update dependencies regularly
- Conduct security audits
