#!/bin/bash

# Market Tracker Test Script
# This script runs all tests for the project

set -e

echo "🧪 Running Market Tracker Tests..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if services are running
echo "🔍 Checking if services are running..."
if ! docker-compose ps | grep -q "Up"; then
    print_warning "Services are not running. Starting them..."
    docker-compose up -d
    sleep 30
fi

# Run linting
echo "🔍 Running linting..."
if command -v ruff &> /dev/null; then
    ruff check . && print_status "Ruff linting passed"
else
    print_warning "Ruff not found, skipping linting"
fi

if command -v black &> /dev/null; then
    black --check . && print_status "Black formatting check passed"
else
    print_warning "Black not found, skipping formatting check"
fi

if command -v mypy &> /dev/null; then
    mypy . && print_status "MyPy type checking passed"
else
    print_warning "MyPy not found, skipping type checking"
fi

# Run unit tests
echo "🧪 Running unit tests..."
cd market-tracker
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if command -v pytest &> /dev/null; then
    pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
    print_status "FastAPI unit tests passed"
else
    print_error "pytest not found, skipping unit tests"
fi

cd ..

# Run ETL tests
echo "🧪 Running ETL tests..."
cd yahoo_etl
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if command -v pytest &> /dev/null; then
    pytest tests/ -v
    print_status "ETL unit tests passed"
else
    print_error "pytest not found, skipping ETL tests"
fi

cd ..

# Run API contract tests
echo "🧪 Running API contract tests..."
if command -v schemathesis &> /dev/null; then
    schemathesis run --base-url=http://localhost:8000 market-tracker/app/main.py
    print_status "API contract tests passed"
else
    print_warning "schemathesis not found, skipping contract tests"
fi

# Run UI tests
echo "🧪 Running UI tests..."
if command -v playwright &> /dev/null; then
    playwright install
    cd market-tracker
    pytest tests/test_ui.py -v
    print_status "UI tests passed"
    cd ..
else
    print_warning "playwright not found, skipping UI tests"
fi

# Run load tests
echo "🧪 Running load tests..."
if command -v k6 &> /dev/null; then
    k6 run tests/load/load_test.js
    print_status "Load tests passed"
else
    print_warning "k6 not found, skipping load tests"
fi

# Run security tests
echo "🧪 Running security tests..."
if command -v zap-baseline.py &> /dev/null; then
    zap-baseline.py -t http://localhost:8000
    print_status "Security tests passed"
else
    print_warning "ZAP not found, skipping security tests"
fi

echo ""
print_status "All tests completed!"
echo ""
echo "📊 Test results:"
echo "  - Unit tests: Check pytest output above"
echo "  - Coverage report: market-tracker/htmlcov/index.html"
echo "  - Load test results: Check k6 output above"
echo ""
