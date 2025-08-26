#!/usr/bin/env python3
"""
Production readiness test runner for FQCN Converter.

This script runs all comprehensive integration tests to validate
production readiness and generates a detailed assessment report.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class ProductionTestRunner:
    """Coordinates execution of all production readiness tests."""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all production readiness tests and generate report."""
        print("=" * 80)
        print("FQCN CONVERTER PRODUCTION READINESS TEST SUITE")
        print("=" * 80)
        print()

        test_suites = [
            {
                "name": "Comprehensive Integration Tests",
                "module": "tests.integration.test_comprehensive_integration",
                "description": "End-to-end testing with real Ansible projects",
            },
            {
                "name": "Stress and Performance Tests",
                "module": "tests.integration.test_stress_performance",
                "description": "Stress testing and performance regression validation",
            },
            {
                "name": "Ansible Compatibility Tests",
                "module": "tests.integration.test_ansible_compatibility",
                "description": "Compatibility across Ansible versions and formats",
            },
            {
                "name": "API Stability Tests",
                "module": "tests.integration.test_api_stability",
                "description": "API stability and backward compatibility validation",
            },
            {
                "name": "API Examples Validation",
                "module": "tests.integration.test_api_examples_validation",
                "description": "Validation of API usage examples and documentation",
            },
            {
                "name": "Production Readiness Assessment",
                "module": "tests.integration.test_production_readiness",
                "description": "Final security, performance, and deployment validation",
            },
        ]

        overall_results = {
            "start_time": self.start_time,
            "test_suites": {},
            "summary": {},
            "recommendations": [],
            "production_ready": False,
        }

        total_passed = 0
        total_failed = 0
        total_tests = 0

        for suite in test_suites:
            print(f"Running {suite['name']}...")
            print(f"Description: {suite['description']}")
            print("-" * 60)

            result = self._run_test_suite(suite["module"])
            overall_results["test_suites"][suite["name"]] = result

            total_tests += result["total"]
            total_passed += result["passed"]
            total_failed += result["failed"]

            if result["success"]:
                print(
                    f"✅ {suite['name']}: PASSED ({result['passed']}/{result['total']} tests)"
                )
            else:
                print(
                    f"❌ {suite['name']}: FAILED ({result['passed']}/{result['total']} tests)"
                )

            print()

        # Calculate overall results
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        overall_results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "success_rate": success_rate,
            "duration": time.time() - self.start_time,
        }

        # Determine production readiness
        overall_results["production_ready"] = (
            success_rate >= 0.95
        )  # 95% pass rate required

        # Generate recommendations
        overall_results["recommendations"] = self._generate_recommendations(
            overall_results
        )

        # Print final summary
        self._print_final_summary(overall_results)

        # Save detailed report
        self._save_report(overall_results)

        return overall_results

    def _run_test_suite(self, module_name: str) -> Dict[str, Any]:
        """Run a specific test suite using pytest."""
        try:
            # Run pytest on the specific module
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                module_name.replace(".", "/") + ".py",
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=/tmp/pytest_report.json",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # Parse pytest JSON report if available
            report_file = Path("/tmp/pytest_report.json")
            if report_file.exists():
                try:
                    with open(report_file) as f:
                        pytest_report = json.load(f)

                    return {
                        "success": result.returncode == 0,
                        "total": pytest_report["summary"]["total"],
                        "passed": pytest_report["summary"].get("passed", 0),
                        "failed": pytest_report["summary"].get("failed", 0),
                        "skipped": pytest_report["summary"].get("skipped", 0),
                        "duration": pytest_report["duration"],
                        "output": result.stdout,
                        "errors": result.stderr,
                    }
                except (json.JSONDecodeError, KeyError):
                    pass

            # Fallback to parsing stdout
            lines = result.stdout.split("\n")
            passed = len([l for l in lines if "PASSED" in l])
            failed = len([l for l in lines if "FAILED" in l])
            total = passed + failed

            return {
                "success": result.returncode == 0,
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "duration": 0,
                "output": result.stdout,
                "errors": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": 600,
                "output": "",
                "errors": "Test suite timed out after 10 minutes",
            }

        except Exception as e:
            return {
                "success": False,
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": 0,
                "output": "",
                "errors": str(e),
            }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        success_rate = results["summary"]["success_rate"]

        if success_rate < 0.95:
            recommendations.append(
                f"Improve test pass rate from {success_rate:.1%} to at least 95% before production release"
            )

        # Check specific test suite results
        for suite_name, suite_result in results["test_suites"].items():
            if not suite_result["success"]:
                recommendations.append(f"Address failures in {suite_name}")

        # Performance recommendations
        total_duration = results["summary"]["duration"]
        if total_duration > 1800:  # 30 minutes
            recommendations.append(
                "Optimize test execution time for faster CI/CD pipeline"
            )

        if not results["production_ready"]:
            recommendations.append(
                "Complete all failing tests before production deployment"
            )

        return recommendations

    def _print_final_summary(self, results: Dict[str, Any]):
        """Print final test summary."""
        print("=" * 80)
        print("PRODUCTION READINESS TEST SUMMARY")
        print("=" * 80)

        summary = results["summary"]

        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Duration: {summary['duration']:.1f} seconds")
        print()

        if results["production_ready"]:
            print("🎉 PRODUCTION READY: All criteria met for production deployment!")
        else:
            print("⚠️  NOT PRODUCTION READY: Address issues before deployment")

        if results["recommendations"]:
            print("\nRecommendations:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"  {i}. {rec}")

        print()
        print("Detailed test results saved to: production_test_report.json")
        print("=" * 80)

    def _save_report(self, results: Dict[str, Any]):
        """Save detailed test report to file."""
        report_file = Path("production_test_report.json")

        with open(report_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Also create a summary report
        summary_file = Path("production_readiness_summary.md")

        with open(summary_file, "w") as f:
            f.write("# FQCN Converter Production Readiness Report\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            summary = results["summary"]
            f.write("## Test Summary\n\n")
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['passed']} ✅\n")
            f.write(f"- **Failed:** {summary['failed']} ❌\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1%}\n")
            f.write(f"- **Duration:** {summary['duration']:.1f} seconds\n\n")

            if results["production_ready"]:
                f.write("## 🎉 Production Status: READY\n\n")
                f.write("All criteria have been met for production deployment.\n\n")
            else:
                f.write("## ⚠️ Production Status: NOT READY\n\n")
                f.write(
                    "Address the following issues before production deployment:\n\n"
                )

            if results["recommendations"]:
                f.write("## Recommendations\n\n")
                for i, rec in enumerate(results["recommendations"], 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")

            f.write("## Test Suite Results\n\n")
            for suite_name, suite_result in results["test_suites"].items():
                status = "✅ PASSED" if suite_result["success"] else "❌ FAILED"
                f.write(f"### {suite_name}: {status}\n\n")
                f.write(f"- Tests: {suite_result['passed']}/{suite_result['total']}\n")
                f.write(f"- Duration: {suite_result['duration']:.1f}s\n\n")


def main():
    """Main entry point for production readiness testing."""
    runner = ProductionTestRunner()

    try:
        results = runner.run_all_tests()

        # Exit with appropriate code
        if results["production_ready"]:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(2)

    except Exception as e:
        print(f"\n\nUnexpected error during test execution: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
