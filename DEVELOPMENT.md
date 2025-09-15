# PwnSafe Development Guide

This guide provides comprehensive information for developing and contributing to the PwnSafe project.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Building and Packaging](#building-and-packaging)
- [Docker Development](#docker-development)
- [CI/CD](#cicd)
- [Contributing](#contributing)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/PwnSafe.git
   cd PwnSafe
   ```

2. **Set up the development environment:**
   ```bash
   chmod +x scripts/setup-dev.sh
   ./scripts/setup-dev.sh
   ```

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Run the application:**
   ```bash
   python pwnsafe.py
   # or
   make run
   ```

## Development Environment

### Prerequisites

- Python 3.9 or higher
- Git
- Make (optional, for using Makefile commands)

### Virtual Environment

The project uses a Python virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate
```

### Dependencies

- **Production dependencies:** `requirements.txt`
- **Development dependencies:** `requirements-dev.txt`

Install all dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Project Structure

```
PwnSafe/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
├── docs/                       # Documentation
├── scripts/                    # Development scripts
│   ├── setup-dev.sh           # Environment setup
│   └── run-tests.sh           # Test runner
├── tests/                      # Test files
│   ├── __init__.py
│   └── test_pwnsafe.py
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── Makefile                    # Development commands
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pwnsafe.py                 # Main application
└── README.md                  # Project documentation
```

## Development Workflow

### Using Make Commands

The project includes a comprehensive Makefile with common development tasks:

```bash
# Show all available commands
make help

# Setup
make install          # Install production dependencies
make install-dev      # Install development dependencies

# Development
make run              # Run the application
make test             # Run tests
make lint             # Run linting
make format           # Format code
make check-all        # Run all checks

# Build & Deploy
make build            # Build executable
make clean            # Clean build artifacts

# Docker
make docker-build     # Build Docker image
make docker-run       # Run in Docker

# Documentation
make docs             # Generate documentation

# Security
make security         # Run security checks
```

### Using Development Scripts

```bash
# Set up development environment
./scripts/setup-dev.sh

# Run tests
./scripts/run-tests.sh [test_type]
# test_type: unit, integration, lint, security, format, all
```

## Testing

### Test Structure

- **Unit tests:** Test individual components in isolation
- **Integration tests:** Test component interactions
- **Security tests:** Check for security vulnerabilities

### Running Tests

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=pwnsafe --cov-report=html

# Using scripts
./scripts/run-tests.sh all
./scripts/run-tests.sh unit
```

### Test Configuration

Tests are configured in `pyproject.toml`:
- Test discovery patterns
- Coverage settings
- Markers for different test types

## Code Quality

### Code Formatting

The project uses Black for code formatting and isort for import sorting:

```bash
# Format code
black pwnsafe.py tests/
isort pwnsafe.py tests/

# Check formatting
black --check pwnsafe.py tests/
isort --check-only pwnsafe.py tests/
```

### Linting

Flake8 and MyPy are used for code quality checks:

```bash
# Run linting
flake8 pwnsafe.py tests/
mypy pwnsafe.py

# Using make
make lint
```

### Pre-commit Hooks

Pre-commit hooks ensure code quality before commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Building and Packaging

### Building Executable

```bash
# Build with PyInstaller
pyinstaller --onefile --windowed --name PwnSafe pwnsafe.py

# Using make
make build
```

### Package Distribution

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Docker Development

### Using Docker

```bash
# Build Docker image
docker build -t pwnsafe:latest .

# Run in Docker
docker run -it --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix pwnsafe:latest

# Using docker-compose
docker-compose up pwnsafe-dev
```

### Docker Compose Services

- **pwnsafe:** Production container
- **pwnsafe-dev:** Development container with tools
- **test-ssh:** Test SSH server for development

## CI/CD

### GitHub Actions

The project uses GitHub Actions for continuous integration:

- **Test:** Run tests on multiple Python versions
- **Build:** Create executable and Docker images
- **Release:** Publish to PyPI on release

### Workflow Triggers

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Release publication

## Contributing

### Development Process

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests and checks:**
   ```bash
   make check-all
   ```
5. **Commit your changes:**
   ```bash
   git commit -m "Add your feature"
   ```
6. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a pull request**

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write comprehensive tests
- Update documentation as needed
- Keep commits atomic and well-described

### Pull Request Guidelines

- Provide a clear description of changes
- Include tests for new functionality
- Ensure all checks pass
- Update documentation if needed
- Follow the existing code style

## Troubleshooting

### Common Issues

1. **Import errors:** Ensure virtual environment is activated
2. **GUI not displaying:** Check X11 forwarding for Docker
3. **Test failures:** Verify all dependencies are installed
4. **Build errors:** Check Python version compatibility

### Getting Help

- Check existing issues on GitHub
- Create a new issue with detailed information
- Include error messages and system information

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
