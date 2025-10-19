# Security Guide

This document outlines security best practices and requirements for the Brownie Metadata API.

## 🔐 Critical Security Requirements

### 1. Environment Variables

**NEVER commit secrets to version control!**

- Copy `env.template` to `.env` and update all values
- Use strong, unique secrets for each environment
- Rotate secrets regularly in production

### 2. JWT Secret

**CRITICAL**: The JWT secret must be changed from the default value!

```bash
# Generate a strong JWT secret
openssl rand -base64 32

# Set in your .env file
METADATA_JWT_SECRET=your-generated-secret-here
```

**Requirements:**
- Minimum 32 characters
- Cryptographically random
- Unique per environment
- Never use default values

### 3. Database Security

**Use certificate authentication in production:**

```bash
# Development (with generated certs)
METADATA_POSTGRES_DSN=postgresql://brownie@localhost:5432/brownie_metadata?sslmode=require&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt

# Production (with Vault PKI)
VAULT_ENABLED=true
VAULT_URL=https://vault.yourcompany.com
VAULT_TOKEN=your-vault-token
```

### 4. CORS Configuration

**Restrict CORS origins in production:**

```bash
# Development
METADATA_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Production
METADATA_CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

## 🛡️ Security Features

### Authentication & Authorization

- **JWT Authentication**: Secure token-based auth with configurable expiration
- **Okta OIDC**: Enterprise SSO integration
- **Role-Based Access Control**: Granular permissions (Admin, Editor, Viewer)
- **Multi-tenant Isolation**: Organization-scoped data access

### Database Security

- **Client Certificate Authentication**: No passwords, uses certificate CN
- **mTLS Support**: Mutual certificate verification in production
- **Encrypted Connections**: All data encrypted in transit
- **Certificate Management**: Vault PKI (production) or local files (development)

### API Security

- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Rate Limiting**: Built-in request throttling
- **Audit Logging**: Track all mutations with user attribution

## 🔧 Development Setup

### 1. Generate Development Certificates

```bash
# Generate self-signed certificates
python scripts/generate_dev_certs.py

# This creates certificates in dev-certs/ directory
```

### 2. Configure Environment

```bash
# Copy template
cp env.template .env

# Edit .env with your values
nano .env
```

### 3. Start with Security Validation

```bash
# The app will validate secrets on startup
uvicorn app.main:app --reload
```

## 🚀 Production Deployment

### 1. Secrets Management

**Use proper secrets management:**

- **Vault**: HashiCorp Vault for PKI and secrets
- **AWS Secrets Manager**: For cloud deployments
- **Kubernetes Secrets**: For containerized deployments
- **Environment Variables**: Only for non-sensitive config

### 2. Certificate Management

**Production certificate setup:**

```bash
# Enable Vault integration
VAULT_ENABLED=true
VAULT_URL=https://vault.yourcompany.com
VAULT_TOKEN=your-vault-token
VAULT_CERT_PATH=secret/brownie-metadata/certs

# Enable mTLS
METADATA_MTLS_ENABLED=true
```

### 3. Security Headers

**Configure security headers in your reverse proxy:**

```nginx
# Nginx example
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

### 4. Monitoring & Logging

**Enable security monitoring:**

- **Structured Logging**: JSON logs with security context
- **Prometheus Metrics**: Request/response monitoring
- **Audit Trails**: Track all data mutations
- **Error Tracking**: Monitor for security issues

## 🚨 Security Checklist

### Before Deployment

- [ ] JWT secret changed from default
- [ ] Database password is strong and unique
- [ ] CORS origins restricted to actual domains
- [ ] Debug mode disabled
- [ ] Certificate authentication enabled
- [ ] Secrets stored in secure vault
- [ ] Security headers configured
- [ ] Monitoring enabled
- [ ] Log levels appropriate for production

### Regular Maintenance

- [ ] Rotate JWT secrets quarterly
- [ ] Rotate database passwords annually
- [ ] Update certificates before expiration
- [ ] Review access logs monthly
- [ ] Update dependencies regularly
- [ ] Conduct security audits

## 🆘 Incident Response

### If Secrets Are Compromised

1. **Immediately rotate all secrets**
2. **Revoke all JWT tokens**
3. **Check access logs for unauthorized access**
4. **Update all environments**
5. **Notify security team**

### Security Contacts

- **Security Team**: security@yourcompany.com
- **On-Call**: +1-XXX-XXX-XXXX
- **Slack**: #security-alerts

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Vault Documentation](https://www.vaultproject.io/docs)
