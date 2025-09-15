#!/bin/bash
# PwnSafe Test Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run setup-dev.sh first."
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
}

# Run different types of tests
run_unit_tests() {
    print_status "Running unit tests..."
    pytest tests/ -v --cov=pwnsafe --cov-report=term-missing
}

run_integration_tests() {
    print_status "Running integration tests..."
    pytest tests/ -v -m integration
}

run_all_tests() {
    print_status "Running all tests..."
    pytest tests/ -v --cov=pwnsafe --cov-report=term-missing --cov-report=html
}

run_lint_tests() {
    print_status "Running linting tests..."
    flake8 pwnsafe.py tests/
    mypy pwnsafe.py
}

run_security_tests() {
    print_status "Running security tests..."
    bandit -r pwnsafe.py
    safety check
}

run_format_check() {
    print_status "Running format check..."
    black --check pwnsafe.py tests/
    isort --check-only pwnsafe.py tests/
}

# Main function
main() {
    case "${1:-all}" in
        "unit")
            check_venv
            activate_venv
            run_unit_tests
            ;;
        "integration")
            check_venv
            activate_venv
            run_integration_tests
            ;;
        "lint")
            check_venv
            activate_venv
            run_lint_tests
            ;;
        "security")
            check_venv
            activate_venv
            run_security_tests
            ;;
        "format")
            check_venv
            activate_venv
            run_format_check
            ;;
        "all")
            check_venv
            activate_venv
            run_format_check
            run_lint_tests
            run_security_tests
            run_all_tests
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [test_type]"
            echo ""
            echo "Test types:"
            echo "  unit        Run unit tests only"
            echo "  integration Run integration tests only"
            echo "  lint        Run linting tests only"
            echo "  security    Run security tests only"
            echo "  format      Run format check only"
            echo "  all         Run all tests (default)"
            echo "  help        Show this help message"
            ;;
        *)
            print_error "Unknown test type: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    print_success "Tests completed successfully!"
}

# Run main function
main "$@"
