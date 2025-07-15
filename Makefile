# Makefile for Mindat Scraper API

.PHONY: help install test clean run-api run-scraper format lint setup

# Default target
help:
	@echo "Mindat Scraper API - Available commands:"
	@echo ""
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up generated files"
	@echo "  run-api     - Start the API server"
	@echo "  run-scraper - Run scraper with example search"
	@echo "  format      - Format code with black"
	@echo "  lint        - Run linting checks"
	@echo "  setup       - Complete setup (install + test)"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run Docker container"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make run-api"
	@echo "  make run-scraper SEARCH='quartz'"
	@echo "  make docker-build"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf data/minerals.json
	rm -rf logs/

# Start API server
run-api:
	python main.py api

# Run scraper with example search
run-scraper:
	python main.py scrape "${SEARCH}"

# Format code
format:
	black . --line-length 88 --target-version py38

# Lint code
lint:
	flake8 . --max-line-length 88 --ignore E203,W503 --exclude .venv,__pycache__

# Complete setup
setup: install test
	@echo "✅ Setup complete!"
	@echo "Run 'make run-api' to start the API server"

# Development server with auto-reload
dev:
	python main.py api --reload

# Example usage
example:
	python scripts/example.py

# Install development dependencies
install-dev:
	pip install black flake8 pytest-cov

# Run tests with coverage
test-coverage:
	python -m pytest tests/ --cov=app --cov-report=html

# Docker commands
docker-build:
	cd infra && docker build -t mindat-scraper-api ..

docker-run:
	cd infra && docker-compose up -d

docker-stop:
	cd infra && docker-compose down

# Run CLI script
cli:
	python scripts/cli.py "${SEARCH}"

# Add sample data
sample-data:
	python scripts/test_api.py

# Check project structure
structure:
	tree -I '__pycache__|.pytest_cache|.venv|*.pyc'
