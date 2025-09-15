#!/bin/bash
# PwnSafe Development Environment Setup Script

set -e

echo "🚀 Setting up PwnSafe development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is not installed. Please install Python 3.9 or higher."
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment and install dependencies
install_deps() {
    print_status "Installing dependencies..."
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install production dependencies
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install -r requirements-dev.txt
    
    print_success "Dependencies installed successfully"
}

# Setup pre-commit hooks
setup_precommit() {
    print_status "Setting up pre-commit hooks..."
    source venv/bin/activate
    pre-commit install
    print_success "Pre-commit hooks installed"
}

# Create test directory structure
setup_tests() {
    print_status "Setting up test structure..."
    mkdir -p tests
    if [ ! -f "tests/__init__.py" ]; then
        touch tests/__init__.py
    fi
    print_success "Test structure created"
}

# Create configuration files
create_configs() {
    print_status "Creating configuration files..."
    
    # Create pytest.ini
    cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
EOF

    # Create pyproject.toml for tool configuration
    cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "pwnsafe"
version = "1.0.0"
description = "A Python-based GUI utility for backup and restore operations on remote systems"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "PwnSafe Team", email = "team@pwnsafe.dev"},
]
keywords = ["backup", "restore", "ssh", "gui", "remote"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: System :: Archiving :: Backup",
    "Topic :: System :: Systems Administration",
]

dependencies = [
    "bcrypt>=4.0.0",
    "cffi>=1.15.0",
    "cryptography>=41.0.0",
    "customtkinter>=5.2.0",
    "darkdetect>=0.8.0",
    "packaging>=23.0",
    "paramiko>=3.3.0",
    "pycparser>=2.21",
    "PyNaCl>=1.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "types-paramiko>=3.0.0",
    "pre-commit>=3.0.0",
    "tox>=4.0.0",
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=2.0.0",
    "pyinstaller>=6.0.0",
    "build>=1.0.0",
    "twine>=4.0.0",
    "bandit>=1.7.0",
    "safety>=3.0.0",
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["pwnsafe"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=pwnsafe",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["pwnsafe"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
EOF

    print_success "Configuration files created"
}

# Main setup function
main() {
    echo "=========================================="
    echo "PwnSafe Development Environment Setup"
    echo "=========================================="
    
    check_python
    setup_venv
    install_deps
    setup_precommit
    setup_tests
    create_configs
    
    echo ""
    echo "=========================================="
    print_success "Development environment setup complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Run the application:"
    echo "   python pwnsafe.py"
    echo "   # or use: make run"
    echo ""
    echo "3. Run tests:"
    echo "   pytest"
    echo "   # or use: make test"
    echo ""
    echo "4. Format code:"
    echo "   black pwnsafe.py"
    echo "   # or use: make format"
    echo ""
    echo "5. Run all checks:"
    echo "   make check-all"
    echo ""
    echo "Happy coding! 🎉"
}

# Run main function
main "$@"
