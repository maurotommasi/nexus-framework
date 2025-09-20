# Makefile for test management
.PHONY: test test-quick test-coverage test-performance test-integration clean-test setup-test

# Default test target
test:
	python run_tests.py all

# Quick smoke tests
test-quick:
	python run_tests.py quick

# Full coverage report
test-coverage:
	python run_tests.py coverage

# Performance benchmarks
test-performance:
	python run_tests.py performance

# Integration tests only
test-integration:
	python -m pytest tests/ -m integration -v

# Validate test environment
test-validate:
	python run_tests.py validate

# Clean test artifacts
clean-test:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf test_data/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Setup test environment
setup-test:
	pip install pytest pytest-cov pytest-benchmark pyyaml psutil requests

# Run specific test file
test-file:
	@read -p "Enter test file pattern: " pattern; \
	python run_tests.py --pattern "$$pattern"

# Generate test report
test-report: test-coverage
	@echo "Test report generated in htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html (macOS) or xdg-open htmlcov/index.html (Linux)"
