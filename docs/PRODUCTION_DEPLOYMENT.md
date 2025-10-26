# Production Deployment Guide

## Database Certificate Authentication

In production, the API server uses certificate-based (mTLS) authentication to connect to PostgreSQL.

### How It Works

1. **Certificates stored in Vault** (production) or local files (development)
2. **API server reads certificates** via `app/cert_manager.py`
3. **Certificates written to temp directory** for psycopg to use
4. **Database connection uses SSL** with certificates

### Production Configuration

Set these environment variables:

```bash
# Enable mTLS for production
METADATA_MTLS_ENABLED=true

# Vault configuration (production)
VAULT_ENABLED=true
VAULT_URL=https://vault.yourcompany.com
VAULT_TOKEN=your-vault-token
VAULT_CERT_PATH=secret/brownie-metadata/certs

# Database connection (will add SSL params automatically)
METADATA_POSTGRES_DSN=postgresql://brownie-fastapi-server@db-host:5432/brownie_metadata
```

### What Happens at Runtime

1. **Settings loaded** via `app/settings.py`
2. **Certificate manager checks** if Vault is enabled
3. **Certificates retrieved** from Vault (production) or local files (dev)
4. **Certificates written** to `/tmp/brownie-certs/` directory
5. **Database URL built** with `sslcert`, `sslkey`, `sslrootcert` parameters
6. **SQLAlchemy engine created** with SSL configuration
7. **Connections use certificates** automatically

### Test vs Production

| Mode | SSL | Source of Certificates |
|------|-----|----------------------|
| **Tests** | Disabled (`sslmode=disable`) | Not used |
| **Development** | Basic (`sslmode=require`) | Local files in `dev-certs/` |
| **Production** | Full mTLS (`sslmode=verify-full`) | HashiCorp Vault |

### Security Notes

- ✅ **Production always uses mTLS** with certificate verification
- ✅ **Certificates stored in Vault**, not in code or environment
- ✅ **Test database doesn't use SSL** (faster, simpler tests)
- ✅ **dev-certs** for local development with self-signed certs

### Troubleshooting

**Error: "SSL connection required"**
- Check that production database has SSL enabled
- Verify certificates are available in Vault

**Error: "certificate verify failed"**
- Check CA certificate matches database server's certificate
- Verify certificate files are readable and valid

**Test failures about SSL**
- Tests should use `sslmode=disable` (which they do)
- Check environment variable `METADATA_POSTGRES_DSN` in CI

