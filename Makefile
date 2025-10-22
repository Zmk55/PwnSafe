# PwnSafe Development Makefile
# Common development tasks for the PwnSafe project

.PHONY: help install install-dev test lint format clean build run docs security check-all

# Default target
help:
	@echo "PwnSafe Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run          Run the PwnSafe application"
	@echo "  test         Run tests with pytest"
	@echo "  lint         Run linting checks (flake8, mypy)"
	@echo "  format       Format code with black and isort"
	@echo "  check-all    Run all checks (lint, format, test, security)"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build        Build executable for current platform"
	@echo "  build-windows Build Windows executable"
	@echo "  build-linux  Build Linux executable"
	@echo "  build-universal Build for current platform with package"
	@echo "  clean        Clean build artifacts and cache"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         Generate documentation"
	@echo ""
	@echo "Security:"
	@echo "  security     Run security checks (bandit, safety)"

# Setup commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Development commands
run:
	python pwnsafe.py

test:
	pytest tests/ -v --cov=pwnsafe --cov-report=html --cov-report=term

lint:
	flake8 pwnsafe.py tests/
	mypy pwnsafe.py

format:
	black pwnsafe.py tests/
	isort pwnsafe.py tests/

check-all: format lint test security
	@echo "All checks completed successfully!"

# Build commands
build:
	python build.py

build-windows:
	python build_windows.py

build-linux:
	python build_linux.py

build-universal:
	python build.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Documentation
docs:
	sphinx-build -b html docs/ docs/_build/html

# Security
security:
	bandit -r pwnsafe.py
	safety check

# Pre-commit setup
setup-pre-commit:
	pre-commit install

# Virtual environment setup
setup-venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Development server with auto-reload (if using watchdog)
dev:
	@echo "Starting development server..."
	python pwnsafe.py

# Package for distribution
package:
	python -m build

# Upload to PyPI (requires credentials)
upload:
	twine upload dist/*

# Check package before upload
check-package:
	twine check dist/*
