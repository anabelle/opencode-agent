#!/bin/bash
# Test runner script for the monitor project

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov

# Show coverage report
echo ""
echo "Coverage report generated in htmlcov/"
echo "Open htmlcov/index.html in your browser to view detailed coverage"