#!/bin/bash
# Code quality check script for the monitor project

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🔍 Running code quality checks..."
echo "================================="

# Run flake8 for linting
echo ""
echo "📝 Running flake8 (linting)..."
flake8 . --count --statistics

# Run black for formatting check
echo ""
echo "🎨 Running black (formatting check)..."
black --check --diff .

# Run isort for import sorting check
echo ""
echo "📦 Running isort (import sorting check)..."
isort --check-only --diff .

# Run tests with coverage
echo ""
echo "🧪 Running tests with coverage..."
python -m pytest tests/ --cov=. --cov-report=term-missing

echo ""
echo "✅ Code quality checks complete!"
echo ""
echo "💡 To fix formatting issues:"
echo "   black ."
echo ""
echo "💡 To fix import sorting:"
echo "   isort ."
echo ""
echo "💡 To see detailed flake8 issues:"
echo "   flake8 . --statistics"