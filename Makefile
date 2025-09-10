# StyleStack Testing Makefile
# Provides convenient commands for running tests with different configurations

.PHONY: help test test-parallel test-unit test-integration test-system test-fast test-slow test-coverage test-benchmark clean install-test-deps

# Default target
help:
	@echo "StyleStack Testing Commands"
	@echo "=========================="
	@echo ""
	@echo "Testing:"
	@echo "  test              Run all tests with default configuration"
	@echo "  test-parallel     Run tests with parallel execution (recommended)"
	@echo "  test-unit         Run unit tests only (fast)"
	@echo "  test-integration  Run integration tests only" 
	@echo "  test-system       Run system tests only (slow)"
	@echo "  test-fast         Run fast tests (unit + fast integration)"
	@echo "  test-slow         Run slow tests (stress + system)"
	@echo "  test-coverage     Run tests with detailed coverage reporting"
	@echo "  test-benchmark    Run performance benchmark of test execution"
	@echo ""
	@echo "Setup:"
	@echo "  install-test-deps Install testing dependencies"
	@echo "  clean             Clean test artifacts and reports"
	@echo ""
	@echo "Examples:"
	@echo "  make test-unit                    # Quick unit test run"
	@echo "  make test-parallel               # Full parallel test run"
	@echo "  make test-coverage              # Coverage analysis"

# Install testing dependencies
install-test-deps:
	@echo "Installing testing dependencies..."
	pip install -r requirements-test.txt

# Clean test artifacts
clean:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf reports/
	rm -rf .coverage
	rm -f coverage.xml
	rm -f tests.log
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Basic test run (sequential)
test:
	@echo "Running tests with default configuration..."
	python -m pytest

# Parallel test execution (recommended)
test-parallel:
	@echo "Running tests with parallel execution..."
	python run_parallel_tests.py

# Unit tests only (fast)
test-unit:
	@echo "Running unit tests..."
	python run_parallel_tests.py --type unit

# Integration tests only
test-integration:
	@echo "Running integration tests..."
	python run_parallel_tests.py --type integration

# System tests only (slow)
test-system:
	@echo "Running system tests..."
	python run_parallel_tests.py --type system

# Fast tests (unit + fast integration)
test-fast:
	@echo "Running fast tests..."
	python run_parallel_tests.py --type fast

# Slow tests (stress + system)
test-slow:
	@echo "Running slow tests..."
	python run_parallel_tests.py --type slow

# Coverage reporting
test-coverage:
	@echo "Running tests with detailed coverage reporting..."
	python run_parallel_tests.py --coverage-threshold 85

# Performance benchmark
test-benchmark:
	@echo "Running performance benchmark..."
	python run_parallel_tests.py --benchmark

# Continuous integration target
ci: clean install-test-deps test-parallel
	@echo "CI testing complete"

# Development target (quick feedback loop)
dev: test-unit
	@echo "Development testing complete"

# Quality assurance target (comprehensive)
qa: clean test-coverage test-slow
	@echo "QA testing complete"