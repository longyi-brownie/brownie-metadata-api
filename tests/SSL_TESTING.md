# SSL Connection Testing Guide

This guide explains how to test SSL/mTLS database connections.

## Overview

The test suite includes:
1. **Unit tests** - Mock-based tests for certificate manager logic
2. **Integration tests** - Real SSL connections to PostgreSQL

## Prerequisites

- OpenSSL installed
- Docker and Docker Compose
- PostgreSQL client tools

## Quick Start

### 1. Generate Development Certificates

```bash
# Generate self-signed certificates for testing
uv run python scripts/generate_dev_certs.py
```

This creates certificates in `dev-certs/`:
- `ca.crt` - Certificate Authority
- `ca.key` - CA private key
- `client.crt` - Client certificate
- `client.key` - Client private key

### 2. Run Unit Tests (No Database Required)

```bash
# Test certificate manager logic with mocks
uv run pytest tests/unit/test_cert_manager.py -v
```

**Expected output:**
```
tests/unit/test_cert_manager.py::TestCertificateManager::test_init_with_vault_enabled PASSED
tests/unit/test_cert_manager.py::TestCertificateManager::test_get_certificate_from_vault PASSED
tests/unit/test_cert_manager.py::TestCertificateManager::test_get_certificate_from_local_file PASSED
...
========== 10 passed in 0.5s ==========
```

### 3. Run Integration Tests (Requires SSL-enabled PostgreSQL)

#### Option A: Use Docker Compose (Recommended)

```bash
# Start SSL-enabled PostgreSQL
docker-compose -f tests/docker-compose.ssl.yml up -d

# Wait for PostgreSQL to be ready
sleep 5

# Set environment variables
export TEST_SSL_ENABLED=true
export METADATA_MTLS_ENABLED=true
export LOCAL_CERT_DIR=dev-certs
export METADATA_POSTGRES_DSN_SSL="postgresql://postgres@localhost:5434/test_brownie_metadata?sslmode=verify-ca&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt"

# Run integration tests
uv run pytest tests/integration/test_ssl_connection.py -v -s

# Cleanup
docker-compose -f tests/docker-compose.ssl.yml down
```

#### Option B: Use Existing PostgreSQL

If you have an SSL-enabled PostgreSQL instance:

```bash
export TEST_SSL_ENABLED=true
export METADATA_MTLS_ENABLED=true
export LOCAL_CERT_DIR=dev-certs
export METADATA_POSTGRES_DSN_SSL="postgresql://your-user@your-host:5432/your-db?sslmode=verify-ca&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt"

uv run pytest tests/integration/test_ssl_connection.py -v
```

## Test Coverage

### Unit Tests (`test_cert_manager.py`)

✅ Certificate manager initialization  
✅ Loading certificates from Vault (mocked)  
✅ Loading certificates from local files  
✅ Handling missing certificates  
✅ Building SSL config for database  
✅ mTLS vs SSL-only modes  
✅ Error handling (connection failures, missing files)  
✅ Base64-encoded certificates  

### Integration Tests (`test_ssl_connection.py`)

✅ Certificate files exist and have correct permissions  
✅ Certificate content is valid PEM format  
✅ Certificate manager loads real certificates  
✅ Database URL includes SSL parameters  
✅ Actual SSL connection to PostgreSQL works  
✅ Connection fails without proper certificates (when mTLS required)  
✅ Connection fails with wrong CA certificate  
✅ Fallback to non-SSL when `sslmode=disable`  

## Troubleshooting

### Certificate Permission Errors

```bash
# Fix private key permissions
chmod 600 dev-certs/client.key
chmod 644 dev-certs/client.crt
chmod 644 dev-certs/ca.crt
```

### PostgreSQL Connection Refused

```bash
# Check if PostgreSQL is running
docker ps | grep postgres-ssl

# Check PostgreSQL logs
docker logs brownie-metadata-postgres-ssl

# Verify port is accessible
nc -zv localhost 5434
```

### SSL Handshake Failures

```bash
# Test SSL connection with psql
psql "postgresql://postgres@localhost:5434/test_brownie_metadata?sslmode=require&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt"

# Check certificate validity
openssl x509 -in dev-certs/client.crt -text -noout

# Verify certificate matches key
openssl x509 -noout -modulus -in dev-certs/client.crt | openssl md5
openssl rsa -noout -modulus -in dev-certs/client.key | openssl md5
```

### Certificate Expired

```bash
# Check certificate expiration
openssl x509 -in dev-certs/client.crt -noout -dates

# Regenerate certificates
rm -rf dev-certs/*
uv run python scripts/generate_dev_certs.py
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: SSL Tests

on: [push, pull_request]

jobs:
  ssl-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      
      - name: Generate certificates
        run: uv run python scripts/generate_dev_certs.py
      
      - name: Run unit tests
        run: uv run pytest tests/unit/test_cert_manager.py -v
      
      - name: Run integration tests (if SSL enabled)
        if: env.TEST_SSL_ENABLED == 'true'
        env:
          TEST_SSL_ENABLED: true
          METADATA_MTLS_ENABLED: true
          LOCAL_CERT_DIR: dev-certs
        run: uv run pytest tests/integration/test_ssl_connection.py -v
```

## Security Notes

⚠️ **Development certificates are self-signed and should NEVER be used in production!**

For production:
1. Use proper CA-signed certificates
2. Store certificates in HashiCorp Vault or similar secret management
3. Rotate certificates regularly
4. Use strong key sizes (4096-bit RSA or 256-bit ECC)
5. Enable certificate revocation checking (CRL/OCSP)

## Additional Resources

- [PostgreSQL SSL Documentation](https://www.postgresql.org/docs/current/ssl-tcp.html)
- [SQLAlchemy SSL Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)
- [OpenSSL Certificate Guide](https://www.openssl.org/docs/man1.1.1/man1/openssl-x509.html)

