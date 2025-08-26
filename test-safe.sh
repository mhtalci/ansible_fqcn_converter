#!/bin/bash

# Safe test runner - excludes tests that might hang
echo "Running safe tests (excluding potentially hanging tests)..."

# Activate virtual environment
source venv/bin/activate

# Exclude problematic test files that use threading, subprocess, or sleep
python -m pytest \
    --ignore=tests/unit/test_logging_complete.py \
    --ignore=tests/run_unit_tests.py \
    --ignore=tests/run_all_tests.py \
    --ignore=tests/run_comprehensive_validation_tests.py \
    --ignore=tests/run_production_readiness_tests.py \
    -k "not (threading or subprocess or sleep or multiprocessing)" \
    --tb=short \
    --maxfail=5 \
    -x \
    -q \
    --disable-warnings \
    tests/

echo "Safe test run completed."