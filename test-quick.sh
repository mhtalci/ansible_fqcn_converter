#!/bin/bash

# Quick test runner - no coverage, unit tests only
echo "Running quick unit tests..."
source venv/bin/activate
python -m pytest tests/unit/ -c pytest-fast.ini -m "not slow" --maxfail=3 -x

echo "Quick test run completed."