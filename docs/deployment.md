# Deployment Guide

## Overview

This guide covers deploying Brownie Metadata API in various environments, from development to production.

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 14+ with SSL support
- SSL certificates for database authentication
- Environment variables configured

## Environment Setup

### Development Environment

```bash
# Clone repositories
git clone https://github.com/your-org/brownie-metadata-api.git
git clone https://github.com/your-org/brownie-metadata-database.git

# Start database
cd brownie-metadata-database
docker-compose up -d

# Start API
cd ../brownie-metadata-api
cp env.example .env
# Edit .env with your configuration
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Staging Environment

```bash
# Build and deploy
docker build -t brownie-metadata-api:staging .
docker run -d \
  --name brownie-metadata-api-staging \
  -p 8080:8080 \
  -e METADATA_POSTGRES_DSN="postgresql://user:pass@staging-db:5432/db?sslmode=require&sslcert=client.crt&sslkey=client.key&sslrootcert=ca.crt" \
  -e METADATA_JWT_SECRET="staging-secret-key" \
  brownie-metadata-api:staging
```

### Production Environment

#### Docker Deployment

```bash
# Build production image
docker build -t brownie-metadata-api:latest .

# Run with production settings
docker run -d \
  --name brownie-metadata-api \
  --restart unless-stopped \
  -p 8080:8080 \
  -e METADATA_POSTGRES_DSN="$PRODUCTION_DATABASE_URL" \
  -e METADATA_JWT_SECRET="$PRODUCTION_JWT_SECRET" \
  -e METADATA_DEBUG="false" \
  -v /path/to/certs:/app/certs:ro \
  brownie-metadata-api:latest
```

#### Kubernetes Deployment

**Namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: brownie-metadata
```

**ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: brownie-metadata-config
  namespace: brownie-metadata
data:
  METADATA_HOST: "0.0.0.0"
  METADATA_PORT: "8080"
  METADATA_DEBUG: "false"
```

**Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: brownie-metadata-secrets
  namespace: brownie-metadata
type: Opaque
data:
  METADATA_POSTGRES_DSN: <base64-encoded-dsn>
  METADATA_JWT_SECRET: <base64-encoded-secret>
```

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brownie-metadata-api
  namespace: brownie-metadata
spec:
  replicas: 3
  selector:
    matchLabels:
      app: brownie-metadata-api
  template:
    metadata:
      labels:
        app: brownie-metadata-api
    spec:
      containers:
      - name: api
        image: brownie-metadata-api:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: brownie-metadata-config
        - secretRef:
            name: brownie-metadata-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: brownie-metadata-api-service
  namespace: brownie-metadata
spec:
  selector:
    app: brownie-metadata-api
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

**Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: brownie-metadata-api-ingress
  namespace: brownie-metadata
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourcompany.com
    secretName: brownie-metadata-tls
  rules:
  - host: api.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: brownie-metadata-api-service
            port:
              number: 80
```

## Scaling

### Horizontal Scaling

**Docker Compose:**
```yaml
version: '3.8'
services:
  api:
    image: brownie-metadata-api:latest
    deploy:
      replicas: 3
    environment:
      - METADATA_POSTGRES_DSN=${METADATA_POSTGRES_DSN}
      - METADATA_JWT_SECRET=${METADATA_JWT_SECRET}
```

**Kubernetes:**
```bash
# Scale deployment
kubectl scale deployment brownie-metadata-api --replicas=5

# Auto-scaling
kubectl autoscale deployment brownie-metadata-api --cpu-percent=70 --min=3 --max=10
```

### Load Balancing

**Nginx Configuration:**
```nginx
upstream brownie_api {
    least_conn;
    server api1:8080 max_fails=3 fail_timeout=30s;
    server api2:8080 max_fails=3 fail_timeout=30s;
    server api3:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.yourcompany.com;
    
    location / {
        proxy_pass http://brownie_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }
    
    location /health {
        access_log off;
        proxy_pass http://brownie_api;
    }
}
```

## Security Configuration

### SSL/TLS

**Certificate Management:**
```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes

# Update Kubernetes secret
kubectl create secret tls brownie-metadata-tls --cert=server.crt --key=server.key
```

### Network Security

**Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5432/tcp  # PostgreSQL (if needed)
ufw enable
```

**Kubernetes Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: brownie-metadata-netpol
  namespace: brownie-metadata
spec:
  podSelector:
    matchLabels:
      app: brownie-metadata-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: postgres
    ports:
    - protocol: TCP
      port: 5432
```

## Monitoring Setup

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s

scrape_configs:
- job_name: 'brownie-metadata-api'
  static_configs:
  - targets: ['api1:8080', 'api2:8080', 'api3:8080']
  metrics_path: /metrics
  scrape_interval: 5s
```

### Grafana Dashboard

**Key Panels:**
- Request rate and error rate
- Response time percentiles
- Database connection pool usage
- Authentication success/failure rates
- JWT token issuance rate

### Alerting Rules

```yaml
groups:
- name: brownie-api
  rules:
  - alert: APIDown
    expr: up{job="brownie-metadata-api"} == 0
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

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_URL="$METADATA_POSTGRES_DSN"

# Create backup
pg_dump "$DB_URL" | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" s3://your-backup-bucket/
```

### Configuration Backup

```bash
#!/bin/bash
# config-backup.sh

CONFIG_DIR="/etc/brownie-metadata"
BACKUP_DIR="/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup configuration files
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" "$CONFIG_DIR"

# Cleanup old config backups (keep 90 days)
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +90 -delete
```

## Maintenance

### Rolling Updates

**Kubernetes:**
```bash
# Update image
kubectl set image deployment/brownie-metadata-api api=brownie-metadata-api:v2.0.0

# Check rollout status
kubectl rollout status deployment/brownie-metadata-api

# Rollback if needed
kubectl rollout undo deployment/brownie-metadata-api
```

**Docker Compose:**
```bash
# Update and restart
docker-compose pull
docker-compose up -d

# Zero-downtime update
docker-compose up -d --no-deps api
```

### Health Checks

```bash
#!/bin/bash
# health-check.sh

API_URL="http://localhost:8080"
HEALTH_ENDPOINT="$API_URL/health"

# Check health
response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT")

if [ "$response" = "200" ]; then
    echo "API is healthy"
    exit 0
else
    echo "API is unhealthy (HTTP $response)"
    exit 1
fi
```

## Troubleshooting

### Common Deployment Issues

1. **Certificate Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in client.crt -noout -dates
   
   # Verify certificate chain
   openssl verify -CAfile ca.crt client.crt
   ```

2. **Database Connection Issues**
   ```bash
   # Test connection
   psql "$METADATA_POSTGRES_DSN" -c "SELECT 1"
   
   # Check network connectivity
   telnet database-host 5432
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats brownie-metadata-api
   
   # Increase memory limits
   docker run --memory=1g brownie-metadata-api
   ```

### Log Analysis

```bash
# View logs
docker logs brownie-metadata-api

# Follow logs
docker logs -f brownie-metadata-api

# Filter error logs
docker logs brownie-metadata-api 2>&1 | grep ERROR

# Kubernetes logs
kubectl logs -f deployment/brownie-metadata-api
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_org_id ON users(org_id);
CREATE INDEX CONCURRENTLY idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;

-- Analyze table statistics
ANALYZE users;
```

### Application Optimization

```python
# Connection pool tuning
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Enable query caching
from sqlalchemy.orm import scoped_session
session = scoped_session(sessionmaker(bind=engine))
```

## Security Hardening

### Container Security

```dockerfile
# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Remove unnecessary packages
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Use specific base image
FROM python:3.11-slim
```

### Runtime Security

```bash
# Run with security options
docker run --security-opt=no-new-privileges \
           --read-only \
           --tmpfs /tmp \
           brownie-metadata-api
```

Remember: This is an enterprise product. All deployments should follow security best practices and be regularly updated and monitored.
