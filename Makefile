# InfoSec Bot Makefile
# Provides convenient commands for development and testing

.PHONY: help install test test-unit test-integration test-security test-performance test-fast test-coverage clean lint format check-security run dev setup-hooks

# Default target
help:
	@echo "InfoSec Bot Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  install       Install dependencies"
	@echo "  setup-hooks   Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-security Run security tests only"
	@echo "  test-performance  Run performance tests only"
	@echo "  test-fast     Run fast tests (exclude slow tests)"
	@echo "  test-coverage Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black and isort"
	@echo "  check-security  Run security checks with bandit"
	@echo ""
	@echo "Development:"
	@echo "  run           Run the application"
	@echo "  dev           Run in development mode with auto-reload"
	@echo "  clean         Clean up generated files"

# Installation
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

setup-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Testing
test:
	./scripts/run_tests.sh all

test-unit:
	./scripts/run_tests.sh unit

test-integration:
	./scripts/run_tests.sh integration

test-security:
	./scripts/run_tests.sh security

test-performance:
	./scripts/run_tests.sh performance

test-fast:
	./scripts/run_tests.sh fast

test-coverage:
	./scripts/run_tests.sh all --coverage

# Code Quality
lint:
	flake8 core/ api/ bot/ --max-line-length=88 --extend-ignore=E203,W503
	mypy core/ api/ bot/ --ignore-missing-imports --no-strict-optional

format:
	black core/ api/ bot/ tests/
	isort core/ api/ bot/ tests/ --profile black

check-security:
	bandit -r core/ api/ bot/ -ll
	safety check

# Development
run:
	python main.py

dev:
	uvicorn main:app --host 127.0.0.1 --port 8080 --reload

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/

# Docker commands (if using Docker)
docker-build:
	docker build -t infosec-bot .

docker-run:
	docker run -p 8080:8080 --env-file .env infosec-bot

docker-test:
	docker run --env-file .env.test infosec-bot pytest

# Database commands
db-migrate:
	python scripts/migrate_database.py

db-seed:
	python scripts/seed_database.py

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-production:
	@echo "Deploying to production..."
	# Add production deployment commands here

# Documentation
docs:
	@echo "Generating documentation..."
	# Add documentation generation commands here

# Health checks
health-check:
	curl -f http://localhost:8080/health || exit 1

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env already exists"; \
	fi

# Full setup for new developers
setup: setup-env install setup-hooks
	@echo "Setup complete! Please:"
	@echo "1. Edit .env with your configuration"
	@echo "2. Run 'make test' to verify everything works"
	@echo "3. Run 'make dev' to start development server"