# Brownie Metadata API Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate seed security-check security-fix

# Default target
help:
	@echo "Available targets:"
	@echo "  install      Install dependencies"
	@echo "  dev          Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linters"
	@echo "  format       Format code"
	@echo "  clean        Clean up temporary files"
	@echo "  docker-build Build Docker image"
	@echo "  docker-up    Start services with Docker Compose"
	@echo "  docker-down  Stop services with Docker Compose"
	@echo "  migrate      Run database migrations"
	@echo "  seed         Seed database with test data"
	@echo "  security-check Run security validation"
	@echo "  security-fix  Fix common security issues"

# Install dependencies
install:
	python3 -m pip install uv
	uv venv
	uv pip install -e .

# Install development dependencies
dev:
	python3 -m pip install uv
	uv venv
	uv pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run linters
lint:
	flake8 app/ tests/
	mypy app/

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Docker commands
docker-build:
	docker build -t brownie-metadata-api .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Database commands
migrate:
	@echo "Database migrations are handled by the brownie-metadata-db package"
	@echo "Run migrations in the database repository, not here"

migrate-create:
	@echo "Database migrations are handled by the brownie-metadata-db package"
	@echo "Create migrations in the database repository, not here"

# Seed database (placeholder)
seed:
	@echo "Seeding database with test data..."
	@echo "This would run a seed script to populate the database with test data"

# Security commands
security-check:
	@echo "Running security validation..."
	python scripts/security_check.py

security-fix:
	@echo "Fixing common security issues..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp env.template .env; \
		echo "⚠️  Please edit .env file with your secrets!"; \
	fi
	@echo "Setting secure file permissions..."
	@find . -name "*.key" -exec chmod 600 {} \; 2>/dev/null || true
	@find . -name "*.crt" -exec chmod 644 {} \; 2>/dev/null || true
	@find . -name "*.pem" -exec chmod 600 {} \; 2>/dev/null || true
	@echo "✅ Security fixes applied!"

# Development setup
setup: install migrate security-fix
	@echo "Development environment setup complete!"
	@echo "Run 'make docker-up' to start the services"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make security-check' to validate security"
