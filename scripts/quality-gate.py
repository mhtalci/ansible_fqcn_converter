#!/usr/bin/env python3
"""
Quality Gate Validation Script

This script runs all quality checks and validates that the code meets
the required standards for production readiness.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class QualityGate:
    """Quality gate validator for the FQCN Converter project."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []

        # Quality thresholds
        self.min_coverage = 95
        self.max_complexity = 10
        self.max_security_issues = 0

    def run_command(
        self, command: List[str], check: bool = True
    ) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=check,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr

    def check_formatting(self) -> bool:
        """Check code formatting with black and isort."""
        print("🎨 Checking code formatting...")

        # Check black formatting
        exit_code, _, stderr = self.run_command(
            ["black", "--check", "--diff", "src", "tests", "scripts"], check=False
        )

        if exit_code != 0:
            self.errors.append("Code formatting check failed (black)")
            return False

        # Check isort formatting
        exit_code, _, stderr = self.run_command(
            ["isort", "--check-only", "--diff", "src", "tests", "scripts"], check=False
        )

        if exit_code != 0:
            self.errors.append("Import sorting check failed (isort)")
            return False

        print("✅ Code formatting check passed")
        return True

    def check_linting(self) -> bool:
        """Check code quality with flake8."""
        print("🔍 Checking code quality...")

        exit_code, stdout, stderr = self.run_command(
            ["flake8", "src", "tests", "scripts", "--statistics"], check=False
        )

        if exit_code != 0:
            self.errors.append(f"Linting check failed:\n{stdout}\n{stderr}")
            return False

        print("✅ Linting check passed")
        return True

    def check_type_annotations(self) -> bool:
        """Check type annotations with mypy."""
        print("🏷️  Checking type annotations...")

        exit_code, stdout, stderr = self.run_command(["mypy", "src"], check=False)

        if exit_code != 0:
            self.errors.append(f"Type checking failed:\n{stdout}\n{stderr}")
            return False

        print("✅ Type checking passed")
        return True

    def check_security(self) -> bool:
        """Check security with bandit."""
        print("🔒 Checking security...")

        # Run bandit with JSON output
        exit_code, stdout, stderr = self.run_command(
            ["bandit", "-r", "src", "-f", "json", "-c", "pyproject.toml"], check=False
        )

        if exit_code != 0:
            try:
                report = json.loads(stdout)
                high_issues = [
                    r
                    for r in report.get("results", [])
                    if r.get("issue_severity") == "HIGH"
                ]
                medium_issues = [
                    r
                    for r in report.get("results", [])
                    if r.get("issue_severity") == "MEDIUM"
                ]

                if len(high_issues) > self.max_security_issues:
                    self.errors.append(
                        f"Security check failed: {len(high_issues)} high severity issues found"
                    )
                    return False

                if len(medium_issues) > self.max_security_issues:
                    print(
                        f"⚠️  Warning: {len(medium_issues)} medium severity issues found"
                    )

            except json.JSONDecodeError:
                self.errors.append(f"Security check failed:\n{stderr}")
                return False

        print("✅ Security check passed")
        return True

    def check_dependencies(self) -> bool:
        """Check dependencies for vulnerabilities."""
        print("📦 Checking dependencies...")

        exit_code, stdout, stderr = self.run_command(
            ["safety", "check", "--json"], check=False
        )

        if exit_code != 0:
            try:
                vulnerabilities = json.loads(stdout)
                if len(vulnerabilities) > self.max_security_issues:
                    self.errors.append(
                        f"Dependency check failed: {len(vulnerabilities)} vulnerabilities found"
                    )
                    return False
            except json.JSONDecodeError:
                # safety might not output JSON on error
                if "No known security vulnerabilities found" not in stderr:
                    self.errors.append(f"Dependency check failed:\n{stderr}")
                    return False

        print("✅ Dependency check passed")
        return True

    def check_coverage(self) -> bool:
        """Check test coverage."""
        print("📊 Checking test coverage...")

        # Run tests with coverage
        exit_code, stdout, stderr = self.run_command(
            [
                "pytest",
                "--cov=fqcn_converter",
                "--cov-report=json",
                f"--cov-fail-under={self.min_coverage}",
            ],
            check=False,
        )

        if exit_code != 0:
            self.errors.append(f"Coverage check failed (minimum {self.min_coverage}%)")
            return False

        # Try to read coverage report
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    total_coverage = coverage_data["totals"]["percent_covered"]
                    print(f"✅ Coverage check passed ({total_coverage:.1f}%)")
            except (json.JSONDecodeError, KeyError):
                print("✅ Coverage check passed")
        else:
            print("✅ Coverage check passed")

        return True

    def check_complexity(self) -> bool:
        """Check code complexity."""
        print("🧮 Checking code complexity...")

        exit_code, stdout, stderr = self.run_command(
            [
                "flake8",
                "src",
                f"--max-complexity={self.max_complexity}",
                "--select=C901",
            ],
            check=False,
        )

        if exit_code != 0:
            self.errors.append(f"Complexity check failed (max {self.max_complexity})")
            return False

        print("✅ Complexity check passed")
        return True

    def check_tests(self) -> bool:
        """Run tests."""
        print("🧪 Running tests...")

        exit_code, stdout, stderr = self.run_command(["pytest", "-v"], check=False)

        if exit_code != 0:
            self.errors.append(f"Tests failed:\n{stdout}\n{stderr}")
            return False

        print("✅ Tests passed")
        return True

    def run_all_checks(self) -> bool:
        """Run all quality gate checks."""
        checks = [
            ("formatting", self.check_formatting),
            ("linting", self.check_linting),
            ("type_annotations", self.check_type_annotations),
            ("security", self.check_security),
            ("dependencies", self.check_dependencies),
            ("complexity", self.check_complexity),
            ("tests", self.check_tests),
            ("coverage", self.check_coverage),
        ]

        print("🚀 Running quality gate checks...\n")

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                self.results[check_name] = result
                if not result:
                    all_passed = False
            except Exception as e:
                self.results[check_name] = False
                self.errors.append(f"{check_name} check failed with exception: {e}")
                all_passed = False
            print()

        return all_passed

    def print_summary(self, passed: bool) -> None:
        """Print quality gate summary."""
        print("=" * 60)
        print("QUALITY GATE SUMMARY")
        print("=" * 60)

        for check_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check_name.replace('_', ' ').title():<20} {status}")

        print("=" * 60)

        if passed:
            print("🎉 QUALITY GATE PASSED!")
            print("All checks have passed successfully.")
        else:
            print("💥 QUALITY GATE FAILED!")
            print("\nErrors found:")
            for error in self.errors:
                print(f"  • {error}")
            print("\nPlease fix the issues and run the quality gate again.")

        print("=" * 60)


def main():
    """Main entry point."""
    quality_gate = QualityGate()

    try:
        passed = quality_gate.run_all_checks()
        quality_gate.print_summary(passed)

        if not passed:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n❌ Quality gate interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Quality gate failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
