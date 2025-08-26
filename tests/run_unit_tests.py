#!/usr/bin/env python3
"""
Unit test runner for FQCN Converter.

This script runs the comprehensive unit test suite with coverage reporting
and provides detailed output for development and CI/CD purposes.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run unit tests with coverage reporting."""
    print("Running FQCN Converter Unit Tests")
    print("=" * 50)

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Install test dependencies if needed
    try:
        import coverage
        import pytest
    except ImportError:
        print("Installing test dependencies...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "pytest",
                "pytest-cov",
                "coverage",
            ],
            check=True,
        )

    # Run tests with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
        "--cov=src/fqcn_converter",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=95",
        "--tb=short",
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=False)

        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("🎉 All unit tests passed with 95%+ coverage!")
            print("Coverage report generated in htmlcov/index.html")
            return 0
        else:
            print("\n" + "=" * 50)
            print("❌ Some tests failed or coverage is below 95%")
            return result.returncode

    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
