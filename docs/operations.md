# Day-2 Operations Guide

## Overview

This guide covers the operational aspects of running Brownie Metadata API in production, including monitoring, scaling, troubleshooting, and maintenance procedures.

## Monitoring & Observability

### Health Checks

The API provides multiple health check endpoints:

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed health check with dependency status
curl http://localhost:8080/health/detailed
```

**Health Check Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T04:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Metrics

Prometheus metrics are available at `/metrics`:

```bash
curl http://localhost:8080/metrics
```

**Key Metrics to Monitor:**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `http_requests_total` | Total HTTP requests by endpoint and status | Error rate > 5% |
| `http_request_duration_seconds` | Request latency | P95 > 1s |
| `database_connections_active` | Active database connections | > 80% of pool |
| `jwt_tokens_issued_total` | JWT tokens issued | Unusual spike |
| `authentication_failures_total` | Authentication failures | > 10/min |

**Sample Prometheus Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Average response time
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Database connection pool usage
database_connections_active / database_connections_max
```

### Logging

Structured JSON logging with configurable levels:

```bash
# View logs
docker logs brownie-metadata-api

# Filter by level
docker logs brownie-metadata-api 2>&1 | jq 'select(.level == "error")'

# Filter by user
docker logs brownie-metadata-api 2>&1 | jq 'select(.user_id == "user-123")'
```

**Log Levels:**
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about application flow
- `WARNING`: Something unexpected happened
- `ERROR`: An error occurred but the application can continue
- `CRITICAL`: A serious error occurred

**Log Fields:**
- `timestamp`: ISO 8601 timestamp
- `level`: Log level
- `logger`: Logger name
- `message`: Log message
- `user_id`: User ID (if applicable)
- `request_id`: Request correlation ID
- `endpoint`: API endpoint
- `method`: HTTP method
- `status_code`: HTTP status code
- `duration_ms`: Request duration

## Scaling

### Horizontal Scaling

The API is stateless and can be horizontally scaled:

```bash
# Docker Compose scaling
docker-compose up --scale api=3

# Kubernetes scaling
kubectl scale deployment brownie-metadata-api --replicas=5
```

**Load Balancer Configuration:**
```nginx
upstream brownie_api {
    server api1:8080;
    server api2:8080;
    server api3:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://brownie_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Scaling

**Connection Pooling:**
```python
# app/db.py
engine = create_engine(
    database_url,
    pool_size=20,          # Base pool size
    max_overflow=30,       # Additional connections
    pool_pre_ping=True,    # Validate connections
    pool_recycle=3600,     # Recycle connections every hour
)
```

**Read Replicas:**
```python
# For read-heavy workloads
read_engine = create_engine(read_replica_url)
write_engine = create_engine(master_url)
```

### Caching

**Redis Integration:**
```python
import redis

redis_client = redis.Redis(
    host='redis-host',
    port=6379,
    db=0,
    decode_responses=True
)

# Cache user data
def get_user_cached(user_id: str):
    cache_key = f"user:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    user = get_user_from_db(user_id)
    redis_client.setex(cache_key, 300, json.dumps(user))  # 5 min TTL
    return user
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

**Symptoms:**
- 500 errors on all endpoints
- "connection failed" in logs
- Health check shows database as unhealthy

**Diagnosis:**
```bash
# Check database connectivity
docker exec brownie-metadata-api psql $METADATA_POSTGRES_DSN -c "SELECT 1"

# Check certificate validity
openssl x509 -in dev-certs/client.crt -noout -dates

# Check database logs
docker logs brownie-metadata-postgres
```

**Solutions:**
- Verify database is running
- Check certificate expiration
- Verify connection string
- Check network connectivity

#### 2. Authentication Issues

**Symptoms:**
- 401 errors on protected endpoints
- "Could not validate credentials" errors
- JWT token validation failures

**Diagnosis:**
```bash
# Check JWT secret
echo $METADATA_JWT_SECRET

# Verify token format
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 -d

# Check token expiration
jwt decode <token> --secret <secret>
```

**Solutions:**
- Verify JWT secret is set correctly
- Check token expiration
- Ensure proper Authorization header format
- Verify user exists and is active

#### 3. Performance Issues

**Symptoms:**
- High response times
- Timeout errors
- High CPU/memory usage

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/health

# Check database performance
docker exec brownie-metadata-postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
docker exec brownie-metadata-postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Solutions:**
- Add database indexes
- Optimize queries
- Increase connection pool size
- Scale horizontally
- Enable query caching

### Performance Tuning

#### Database Optimization

**Indexes:**
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_team_id ON users(team_id);

-- Soft deletes
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
```

**Query Optimization:**
```python
# Use select_related for foreign keys
users = db.query(User).options(selectinload(User.organization)).all()

# Use pagination for large datasets
users = db.query(User).offset(offset).limit(limit).all()
```

#### Application Optimization

**Async Operations:**
```python
# Use async for I/O operations
async def get_user_async(user_id: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
```

**Connection Pooling:**
```python
# Optimize connection pool
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Disable SQL logging in production
)
```

## Maintenance

### Regular Tasks

#### Daily
- [ ] Check health endpoints
- [ ] Review error logs
- [ ] Monitor metrics dashboard
- [ ] Check certificate expiration

#### Weekly
- [ ] Review performance metrics
- [ ] Check database disk usage
- [ ] Review security logs
- [ ] Update dependencies

#### Monthly
- [ ] Rotate JWT secrets
- [ ] Update certificates
- [ ] Review and optimize queries
- [ ] Security audit

### Backup Procedures

**Database Backup:**
```bash
# Full backup
pg_dump $METADATA_POSTGRES_DSN > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $METADATA_POSTGRES_DSN | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

**Configuration Backup:**
```bash
# Backup environment files
cp .env .env.backup.$(date +%Y%m%d)
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d)
```

### Security Maintenance

**Certificate Rotation:**
```bash
# Generate new certificates
./scripts/generate_dev_certs.py

# Update environment variables
export METADATA_POSTGRES_DSN="postgresql://user@host:5432/db?sslcert=new-client.crt&sslkey=new-client.key&sslrootcert=new-ca.crt"

# Restart services
docker-compose restart
```

**JWT Secret Rotation:**
```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# Update environment
export METADATA_JWT_SECRET="$NEW_SECRET"

# Restart API
docker-compose restart api
```

## Alerting

### Critical Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| API Down | Health check fails | Page on-call engineer |
| High Error Rate | 5xx errors > 5% | Investigate immediately |
| Database Down | DB health check fails | Check database service |
| High Response Time | P95 > 2s | Check performance |
| Authentication Failures | > 50 failures/min | Security investigation |

### Warning Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| High CPU Usage | > 80% for 5min | Monitor and scale |
| High Memory Usage | > 85% for 5min | Check for memory leaks |
| Connection Pool Exhaustion | > 90% pool usage | Scale or optimize |
| Certificate Expiration | < 30 days | Schedule rotation |

### Alert Configuration

**Prometheus Alert Rules:**
```yaml
groups:
- name: brownie-api
  rules:
  - alert: APIDown
    expr: up{job="brownie-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Brownie API is down"
      
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
```

## Disaster Recovery

### Recovery Procedures

**Database Recovery:**
```bash
# Restore from backup
psql $METADATA_POSTGRES_DSN < backup_20251024_120000.sql

# Verify data integrity
psql $METADATA_POSTGRES_DSN -c "SELECT COUNT(*) FROM users;"
```

**Service Recovery:**
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Verify health
curl http://localhost:8080/health
```

### RTO/RPO Targets

- **Recovery Time Objective (RTO)**: 15 minutes
- **Recovery Point Objective (RPO)**: 5 minutes
- **Availability Target**: 99.9% (8.76 hours downtime/year)

## Support Contacts

- **On-Call Engineer**: +1-555-ONCALL
- **Database Team**: db-team@company.com
- **Security Team**: security@company.com
- **Infrastructure Team**: infra@company.com

## Runbooks

### Incident Response

1. **Assess Impact**
   - Check health endpoints
   - Review error logs
   - Identify affected users

2. **Contain Issue**
   - Scale up if needed
   - Enable maintenance mode if necessary
   - Isolate affected components

3. **Resolve Issue**
   - Apply fixes
   - Restart services if needed
   - Verify resolution

4. **Post-Incident**
   - Document incident
   - Update runbooks
   - Conduct post-mortem

### Escalation Procedures

1. **Level 1**: On-call engineer (0-15 min)
2. **Level 2**: Senior engineer (15-30 min)
3. **Level 3**: Engineering manager (30+ min)
4. **Level 4**: CTO (1+ hour)

Remember: This is an enterprise product. All operational procedures should be documented, tested, and regularly updated.
