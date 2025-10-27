# GitHub Actions Workflows

This directory contains CI/CD workflows for the Brownie Metadata API.

## Workflows

### 1. `ci-cd.yml` - Main CI/CD Pipeline

**Triggers**: Push/PR to `main` or `develop` branches

**What it does**:
- ✅ Linting (ruff)
- ✅ Security checks (bandit, safety)
- ✅ Unit tests (with mocks)
- ✅ Integration tests (with PostgreSQL)
- ✅ Code coverage (60%+ required)
- ✅ Docker build
- ✅ Deployment (on main branch)

**PostgreSQL Setup**:
- Uses GitHub Actions service container
- PostgreSQL 14 without SSL (`sslmode=disable`)
- Fast and reliable for standard tests

**SSL Tests**: ⏭️ **Skipped** (SSL integration tests require SSL-enabled PostgreSQL)

---

### 2. `ssl-tests.yml` - SSL Integration Tests

**Triggers**: 
- Manual workflow dispatch
- Weekly schedule (Sundays 2 AM UTC)

**What it does**:
- ✅ Generates SSL certificates
- ✅ Starts SSL-enabled PostgreSQL (Docker Compose)
- ✅ Runs certificate manager unit tests
- ✅ Runs SSL integration tests
- ✅ Validates SSL connections

**Why separate workflow?**:
1. **Complexity**: SSL setup requires custom PostgreSQL configuration
2. **Speed**: SSL tests are slower (certificate generation, SSL handshake)
3. **Reliability**: Main CI stays fast and stable
4. **Flexibility**: Can run SSL tests on-demand

---

## Test Coverage by Workflow

### Main CI (`ci-cd.yml`)

| Test Suite | Coverage | Status |
|------------|----------|--------|
| Unit tests | All | ✅ Running |
| Integration tests | Non-SSL | ✅ Running |
| Auth tests | All | ✅ Running |
| CRUD tests | All | ✅ Running |
| **SSL tests** | **Skipped** | ⏭️ See `ssl-tests.yml` |

**Result**: ~60% code coverage, all core functionality tested

### SSL Tests (`ssl-tests.yml`)

| Test Suite | Coverage | Status |
|------------|----------|--------|
| Certificate manager | Unit tests | ✅ Running |
| SSL connections | Integration | ✅ Running |
| mTLS validation | Integration | ✅ Running |
| Certificate errors | Integration | ✅ Running |

**Result**: Certificate handling fully validated

---

## Running Workflows

### Main CI (Automatic)

Runs automatically on every push/PR:
```bash
git push origin feature-branch
# CI runs automatically
```

### SSL Tests (Manual)

Run manually from GitHub Actions UI:
1. Go to **Actions** tab
2. Select **SSL Integration Tests**
3. Click **Run workflow**
4. Select branch
5. Click **Run workflow**

Or via GitHub CLI:
```bash
gh workflow run ssl-tests.yml
```

---

## Local Testing

### Run Main Tests Locally

```bash
# Start PostgreSQL (no SSL)
docker-compose -f tests/docker-compose.test.yml up -d

# Set environment
export METADATA_POSTGRES_DSN="postgresql://postgres:postgres@localhost:5433/test_brownie_metadata?sslmode=disable"
export METADATA_JWT_SECRET="test-jwt-secret-key-for-testing-only"

# Run tests
uv run pytest tests/ -v --cov=app
```

### Run SSL Tests Locally

```bash
# Generate certificates
uv run python scripts/generate_dev_certs.py

# Start SSL-enabled PostgreSQL
docker-compose -f tests/docker-compose.ssl.yml up -d

# Set environment
export TEST_SSL_ENABLED=true
export METADATA_MTLS_ENABLED=true
export LOCAL_CERT_DIR=dev-certs
export METADATA_POSTGRES_DSN_SSL="postgresql://postgres@localhost:5434/test_brownie_metadata?sslmode=verify-ca&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt"

# Run SSL tests
uv run pytest tests/unit/test_cert_manager.py -v
uv run pytest tests/integration/test_ssl_connection.py -v
```

---

## Why This Approach?

### ✅ Advantages

1. **Fast CI**: Main CI completes in ~2-3 minutes
2. **Reliable**: No complex SSL setup in main pipeline
3. **Comprehensive**: SSL still tested, just separately
4. **Flexible**: Can run SSL tests on-demand
5. **Clear**: Separation of concerns

### 🤔 Alternatives Considered

#### Option A: SSL in Main CI
❌ **Rejected**: Too complex, slows down every PR

#### Option B: No SSL Tests
❌ **Rejected**: SSL is critical for production

#### Option C: Manual SSL Tests Only
❌ **Rejected**: Easy to forget, no automation

#### ✅ Option D: Separate Workflow (Chosen)
Best of both worlds: Fast main CI + automated SSL validation

---

## Troubleshooting

### Main CI Failing

**Check**:
1. Linting errors: `uv run ruff check .`
2. Test failures: `uv run pytest tests/ -v`
3. Coverage: Must be ≥50%

### SSL Tests Failing

**Common Issues**:

1. **Certificate generation failed**
   ```bash
   # Check OpenSSL is available
   openssl version
   ```

2. **PostgreSQL won't start**
   ```bash
   # Check Docker logs
   docker logs brownie-metadata-postgres-ssl
   ```

3. **SSL connection refused**
   ```bash
   # Verify certificates
   ls -la dev-certs/
   openssl x509 -in dev-certs/client.crt -text -noout
   ```

4. **Tests skipped**
   - Ensure `TEST_SSL_ENABLED=true`
   - Ensure certificates exist in `dev-certs/`

---

## Adding New Tests

### Add to Main CI

Add test files to:
- `tests/` - Unit tests
- `tests/integration/` - Integration tests (non-SSL)

Tests run automatically on every PR.

### Add to SSL Tests

Add test files to:
- `tests/unit/test_cert_manager.py` - Certificate logic
- `tests/integration/test_ssl_connection.py` - SSL connections

Mark with decorator:
```python
@pytest.mark.skipif(
    not _ssl_enabled(),
    reason="Requires SSL-enabled PostgreSQL"
)
```

---

## CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Push/PR to main/develop                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Main CI/CD    │
                    │  (ci-cd.yml)   │
                    └────────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
          ┌─────────┐  ┌─────────┐  ┌─────────┐
          │ Linting │  │  Tests  │  │ Security│
          │  ruff   │  │ pytest  │  │ bandit  │
          └────┬────┘  └────┬────┘  └────┬────┘
               │            │            │
               └────────────┼────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Coverage    │
                     │  ≥50% ✅     │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Docker Build │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Deploy     │
                     │ (main only)  │
                     └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Manual Trigger or Weekly Schedule               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   SSL Tests    │
                    │(ssl-tests.yml) │
                    └────────┬───────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Generate │  │  Start   │  │   Run    │
        │  Certs   │  │ SSL PG   │  │SSL Tests │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Validate   │
                    │ SSL Security │
                    └──────────────┘
```

---

## Security Notes

⚠️ **Important**:
- Certificates in CI are **self-signed** and **temporary**
- Never commit real certificates to git
- Production uses Vault for certificate management
- SSL tests validate logic, not production certificates

---

## Questions?

See:
- `tests/SSL_TESTING.md` - Detailed SSL testing guide
- `SSL_TEST_SUMMARY.md` - SSL test coverage summary
- GitHub Actions logs for specific failures

