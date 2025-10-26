# Production Deployment

## Quick Start

### Required Environment Variables

```bash
# Database - use SSL in production
METADATA_POSTGRES_DSN=postgresql://brownie-fastapi-server@db-host:5432/brownie_metadata?sslmode=require&sslcert=client.crt&sslkey=client.key&sslrootcert=ca.crt

# JWT Secret - generate with: openssl rand -base64 32
METADATA_JWT_SECRET=your-strong-secret-here

# Server Configuration
METADATA_DEBUG=false
METADATA_HOST=0.0.0.0
METADATA_PORT=8080

# CORS - restrict to your domains
METADATA_CORS_ORIGINS=["https://yourdomain.com"]
```

### Docker Deployment

```bash
# Build image
docker build -t brownie-metadata-api .

# Run container
docker run -d \
  --name brownie-api \
  -e METADATA_POSTGRES_DSN="$METADATA_POSTGRES_DSN" \
  -e METADATA_JWT_SECRET="$METADATA_JWT_SECRET" \
  -p 8080:8080 \
  brownie-metadata-api
```

### Kubernetes Deployment

See `infrastructure/kubernetes/` for manifests.

## Certificate Authentication

Production uses certificate-based (mTLS) authentication for database connections.

**Configuration:**
1. Store certificates in HashiCorp Vault or environment
2. Configure `VAULT_ENABLED=true` for Vault integration
3. API automatically uses certificates from Vault or local files

**Security:**
- ✅ No database passwords in production
- ✅ All connections encrypted with SSL
- ✅ Certificate-based authentication
- ✅ Audit logging for all operations

See [Security Guide](./SECURITY.md) for details.

## Monitoring

**Health Check:** `GET /health`

**Metrics:** `GET /metrics` (Prometheus format)

**Logs:** Structured JSON logs to stdout

## Scaling

- **Stateless API** - scale horizontally by adding instances
- **Database connection pooling** - handles 100+ concurrent connections
- **Load balancer ready** - configure health check on `/health` endpoint
