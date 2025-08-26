#!/bin/bash

# Ultra-quick test runner - no coverage, maximum speed
echo "Running ultra-fast tests (no coverage)..."

# Activate virtual environment
source venv/bin/activate

# Use the ultra-fast configuration
python -m pytest -c pytest-ultra-fast.ini tests/ --tb=line -q --disable-warnings --maxfail=3

echo "Ultra-fast test run completed."