.PHONY: help install generate clean lint format test test-unit test-integration coverage run build dev-setup

# Default target
help:
	@echo \"Available targets:\"
	@echo \"  install         - Install dependencies using poetry\"
	@echo \"  clean           - Clean generated files and caches\"
	@echo \"  lint            - Run linting tools\"
	@echo \"  format          - Format code using black and isort\"
	@echo \"  test            - Run all tests\"
	@echo \"  test-unit       - Run unit tests only\"
	@echo \"  test-integration - Run integration tests only\"
	@echo \"  coverage        - Run tests with coverage report\"
	@echo \"  run             - Run the microservice\"
	@echo \"  build           - Build the package\"
	@echo \"  dev-setup       - Set up development environment\"

# Install dependencies
install:
	poetry install

# Clean generated files and caches
clean:
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name \"__pycache__\" -exec rm -rf {} +
	find . -type f -name \"*.pyc\" -delete

# Run linting
lint:
	poetry run flake8 src/ tests/
	poetry run mypy src/

# Format code
format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Run all tests
test:
	poetry run pytest

# Run unit tests only
test-unit:
	poetry run pytest tests/unit/

# Run integration tests only
test-integration:
	poetry run pytest tests/integration/

# Run tests with coverage report
coverage:
	poetry run pytest --cov=src/py_micro/service --cov-report=html --cov-report=term-missing
	@echo \"Coverage report generated in htmlcov/index.html\"

# Run the microservice
run:
	poetry run microservice

# Build package
build:
	poetry build

# Set up development environment
dev-setup: install
	@echo \"Development environment setup complete!\"
	@echo \"Run 'make test' to verify everything works\"
	@echo \"Run 'make run' to start the microservice\"

# Development commands
dev-run:
	poetry run python -m py_micro.service.main

dev-test-watch:
	poetry run pytest-watch

# Docker commands
docker-build:
	docker build -t py-micro-service .

docker-run:
	docker run -p 50051:50051 py-micro-service

