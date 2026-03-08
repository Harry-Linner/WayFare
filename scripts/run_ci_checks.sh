#!/bin/bash
# Run all CI checks locally before pushing
# This script mimics what runs in GitHub Actions

set -e  # Exit on error

echo "🚀 Running CI checks locally..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2 passed${NC}"
    else
        echo -e "${RED}✗ $2 failed${NC}"
        return 1
    fi
}

# Track overall status
OVERALL_STATUS=0

# 1. Check code formatting with Black
echo "📝 Checking code formatting with Black..."
if black --check --diff wayfare/ nanobot/ tests/; then
    print_status 0 "Black formatting"
else
    print_status 1 "Black formatting"
    OVERALL_STATUS=1
    echo -e "${YELLOW}💡 Run 'black wayfare/ nanobot/ tests/' to fix${NC}"
fi
echo ""

# 2. Run Ruff linter
echo "🔍 Running Ruff linter..."
if ruff check wayfare/ nanobot/ tests/; then
    print_status 0 "Ruff linting"
else
    print_status 1 "Ruff linting"
    OVERALL_STATUS=1
    echo -e "${YELLOW}💡 Run 'ruff check --fix wayfare/ nanobot/ tests/' to fix${NC}"
fi
echo ""

# 3. Run type checking with mypy (non-blocking)
echo "🔎 Running type checking with mypy..."
if mypy wayfare/ --ignore-missing-imports --no-strict-optional; then
    print_status 0 "mypy type checking"
else
    echo -e "${YELLOW}⚠ mypy found issues (non-blocking)${NC}"
fi
echo ""

# 4. Run Pylint (non-blocking)
echo "🔬 Running Pylint..."
if pylint wayfare/ --disable=C0111,R0903,W0212,C0103 --max-line-length=100; then
    print_status 0 "Pylint"
else
    echo -e "${YELLOW}⚠ Pylint found issues (non-blocking)${NC}"
fi
echo ""

# 5. Run unit tests
echo "🧪 Running unit tests..."
if pytest tests/ -v --tb=short --ignore=tests/wayfare/test_serialization_roundtrip.py; then
    print_status 0 "Unit tests"
else
    print_status 1 "Unit tests"
    OVERALL_STATUS=1
fi
echo ""

# 6. Run property-based tests
echo "🎲 Running property-based tests..."
if pytest tests/wayfare/test_serialization_roundtrip.py -v --tb=short; then
    print_status 0 "Property-based tests"
else
    print_status 1 "Property-based tests"
    OVERALL_STATUS=1
fi
echo ""

# 7. Check if Qdrant is running for integration tests
echo "🔌 Checking Qdrant connection..."
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Qdrant is running${NC}"
    
    # Run integration tests
    echo "🔗 Running integration tests..."
    if QDRANT_URL=http://localhost:6333 pytest tests/wayfare/ -v --tb=short -k "integration"; then
        print_status 0 "Integration tests"
    else
        print_status 1 "Integration tests"
        OVERALL_STATUS=1
    fi
else
    echo -e "${YELLOW}⚠ Qdrant is not running, skipping integration tests${NC}"
    echo -e "${YELLOW}💡 Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest${NC}"
fi
echo ""

# 8. Generate coverage report (optional)
echo "📊 Generating coverage report..."
if pytest tests/ --cov=wayfare --cov=nanobot --cov-report=term --cov-report=html; then
    print_status 0 "Coverage report"
    echo -e "${GREEN}📈 Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "${YELLOW}⚠ Coverage report generation failed (non-blocking)${NC}"
fi
echo ""

# Final status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All CI checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some CI checks failed. Please fix before pushing.${NC}"
    exit 1
fi
