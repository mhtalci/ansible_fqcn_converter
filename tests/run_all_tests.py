#!/usr/bin/env python3
"""
Comprehensive test runner for FQCN Converter.

This script runs all test suites including unit tests, integration tests,
performance tests, and generates comprehensive coverage reports.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class TestRunner:
    """Comprehensive test runner for all test suites."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: Dict[str, Any] = {}

    def run_unit_tests(self, coverage: bool = True, fail_under: int = 95) -> bool:
        """Run unit tests with optional coverage reporting."""
        print("\n" + "=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)

        cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"]

        if coverage:
            cmd.extend(
                [
                    "--cov=src/fqcn_converter",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov/unit",
                    f"--cov-fail-under={fail_under}",
                ]
            )

        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        duration = time.time() - start_time

        success = result.returncode == 0
        self.results["unit_tests"] = {
            "success": success,
            "duration": duration,
            "command": " ".join(cmd),
        }

        if success:
            print(f"✅ Unit tests passed in {duration:.2f} seconds")
        else:
            print(f"❌ Unit tests failed after {duration:.2f} seconds")

        return success

    def run_integration_tests(self, coverage: bool = True) -> bool:
        """Run integration tests."""
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 60)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "-x",  # Stop on first failure for integration tests
        ]

        if coverage:
            cmd.extend(
                [
                    "--cov=src/fqcn_converter",
                    "--cov-append",  # Append to existing coverage
                    "--cov-report=html:htmlcov/integration",
                ]
            )

        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        duration = time.time() - start_time

        success = result.returncode == 0
        self.results["integration_tests"] = {
            "success": success,
            "duration": duration,
            "command": " ".join(cmd),
        }

        if success:
            print(f"✅ Integration tests passed in {duration:.2f} seconds")
        else:
            print(f"❌ Integration tests failed after {duration:.2f} seconds")

        return success

    def run_performance_tests(self, timeout: int = 300) -> bool:
        """Run performance tests with timeout."""
        print("\n" + "=" * 60)
        print("RUNNING PERFORMANCE TESTS")
        print("=" * 60)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/performance/",
            "-v",
            "--tb=short",
            f"--timeout={timeout}",
        ]

        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        duration = time.time() - start_time

        success = result.returncode == 0
        self.results["performance_tests"] = {
            "success": success,
            "duration": duration,
            "command": " ".join(cmd),
        }

        if success:
            print(f"✅ Performance tests passed in {duration:.2f} seconds")
        else:
            print(f"❌ Performance tests failed after {duration:.2f} seconds")

        return success

    def run_linting(self) -> bool:
        """Run code linting checks."""
        print("\n" + "=" * 60)
        print("RUNNING LINTING CHECKS")
        print("=" * 60)

        success = True

        # Run flake8
        print("Running flake8...")
        flake8_cmd = [sys.executable, "-m", "flake8", "src/", "tests/"]
        flake8_result = subprocess.run(flake8_cmd, cwd=self.project_root)

        if flake8_result.returncode == 0:
            print("✅ flake8 passed")
        else:
            print("❌ flake8 failed")
            success = False

        # Run mypy (if available)
        try:
            print("Running mypy...")
            mypy_cmd = [sys.executable, "-m", "mypy", "src/fqcn_converter/"]
            mypy_result = subprocess.run(mypy_cmd, cwd=self.project_root)

            if mypy_result.returncode == 0:
                print("✅ mypy passed")
            else:
                print("❌ mypy failed")
                success = False
        except FileNotFoundError:
            print("⚠️  mypy not available, skipping type checking")

        self.results["linting"] = {"success": success}
        return success

    def run_security_checks(self) -> bool:
        """Run security checks."""
        print("\n" + "=" * 60)
        print("RUNNING SECURITY CHECKS")
        print("=" * 60)

        success = True

        # Run bandit (if available)
        try:
            print("Running bandit...")
            bandit_cmd = [sys.executable, "-m", "bandit", "-r", "src/"]
            bandit_result = subprocess.run(bandit_cmd, cwd=self.project_root)

            if bandit_result.returncode == 0:
                print("✅ bandit passed")
            else:
                print("❌ bandit found security issues")
                success = False
        except FileNotFoundError:
            print("⚠️  bandit not available, skipping security checks")

        # Run safety (if available)
        try:
            print("Running safety...")
            safety_cmd = [sys.executable, "-m", "safety", "check"]
            safety_result = subprocess.run(safety_cmd, cwd=self.project_root)

            if safety_result.returncode == 0:
                print("✅ safety passed")
            else:
                print("❌ safety found vulnerabilities")
                success = False
        except FileNotFoundError:
            print("⚠️  safety not available, skipping dependency vulnerability checks")

        self.results["security"] = {"success": success}
        return success

    def generate_combined_coverage_report(self) -> None:
        """Generate combined coverage report from all test runs."""
        print("\n" + "=" * 60)
        print("GENERATING COMBINED COVERAGE REPORT")
        print("=" * 60)

        try:
            # Combine coverage data
            combine_cmd = [sys.executable, "-m", "coverage", "combine"]
            subprocess.run(combine_cmd, cwd=self.project_root)

            # Generate HTML report
            html_cmd = [
                sys.executable,
                "-m",
                "coverage",
                "html",
                "-d",
                "htmlcov/combined",
            ]
            subprocess.run(html_cmd, cwd=self.project_root)

            # Generate terminal report
            report_cmd = [sys.executable, "-m", "coverage", "report"]
            subprocess.run(report_cmd, cwd=self.project_root)

            print("✅ Combined coverage report generated in htmlcov/combined/")

        except Exception as e:
            print(f"⚠️  Failed to generate combined coverage report: {e}")

    def print_summary(self) -> bool:
        """Print test summary and return overall success status."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        overall_success = True
        total_duration = 0

        for test_type, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result.get("duration", 0)
            total_duration += duration

            print(
                f"{test_type.replace('_', ' ').title():<20} {status:<8} ({duration:.2f}s)"
            )

            if not result["success"]:
                overall_success = False

        print("-" * 60)
        print(f"{'Total Duration':<20} {total_duration:.2f}s")
        print(f"{'Overall Status':<20} {'✅ PASS' if overall_success else '❌ FAIL'}")

        if overall_success:
            print("\n🎉 All tests passed! The project is ready for production.")
        else:
            print("\n💥 Some tests failed. Please review the output above.")

        return overall_success

    def install_test_dependencies(self) -> bool:
        """Install test dependencies if needed."""
        print("Checking test dependencies...")

        dependencies = [
            "pytest",
            "pytest-cov",
            "pytest-timeout",
            "coverage",
            "psutil",  # For performance monitoring
        ]

        optional_dependencies = ["flake8", "mypy", "bandit", "safety"]

        # Install required dependencies
        for dep in dependencies:
            try:
                __import__(dep.replace("-", "_"))
            except ImportError:
                print(f"Installing {dep}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep], capture_output=True
                )

                if result.returncode != 0:
                    print(f"❌ Failed to install {dep}")
                    return False

        # Install optional dependencies (don't fail if they can't be installed)
        for dep in optional_dependencies:
            try:
                __import__(dep.replace("-", "_"))
            except ImportError:
                print(f"Installing optional dependency {dep}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep], capture_output=True
                )

        print("✅ Test dependencies ready")
        return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run FQCN Converter test suite")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration-only", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--performance-only", action="store_true", help="Run only performance tests"
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Skip coverage reporting"
    )
    parser.add_argument("--no-lint", action="store_true", help="Skip linting checks")
    parser.add_argument(
        "--no-security", action="store_true", help="Skip security checks"
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=95,
        help="Minimum coverage percentage (default: 95)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for performance tests in seconds (default: 300)",
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Initialize test runner
    runner = TestRunner(project_root)

    print("FQCN Converter Test Suite")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")

    # Install dependencies
    if not runner.install_test_dependencies():
        print("❌ Failed to install test dependencies")
        return 1

    overall_success = True

    # Run selected test suites
    if args.unit_only:
        success = runner.run_unit_tests(
            coverage=not args.no_coverage, fail_under=args.fail_under
        )
        overall_success = success
    elif args.integration_only:
        success = runner.run_integration_tests(coverage=not args.no_coverage)
        overall_success = success
    elif args.performance_only:
        success = runner.run_performance_tests(timeout=args.timeout)
        overall_success = success
    else:
        # Run all test suites
        success = runner.run_unit_tests(
            coverage=not args.no_coverage, fail_under=args.fail_under
        )
        overall_success = success

        if success:  # Only run integration tests if unit tests pass
            success = runner.run_integration_tests(coverage=not args.no_coverage)
            overall_success = overall_success and success

        if success:  # Only run performance tests if previous tests pass
            success = runner.run_performance_tests(timeout=args.timeout)
            overall_success = overall_success and success

        # Run quality checks
        if not args.no_lint:
            lint_success = runner.run_linting()
            overall_success = overall_success and lint_success

        if not args.no_security:
            security_success = runner.run_security_checks()
            overall_success = overall_success and security_success

        # Generate combined coverage report
        if not args.no_coverage:
            runner.generate_combined_coverage_report()

    # Print summary
    final_success = runner.print_summary()

    return 0 if final_success else 1


if __name__ == "__main__":
    sys.exit(main())
