# Brownie Metadata API Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate seed

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

# Install dependencies
install:
	pip install uv
	uv pip install -e .

# Install development dependencies
dev:
	pip install uv
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
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(message)"

# Seed database (placeholder)
seed:
	@echo "Seeding database with test data..."
	@echo "This would run a seed script to populate the database with test data"

# Development setup
setup: install migrate
	@echo "Development environment setup complete!"
	@echo "Run 'make docker-up' to start the services"
	@echo "Run 'make test' to run tests"
