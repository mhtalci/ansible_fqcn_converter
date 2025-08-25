#!/usr/bin/env python3
"""
Comprehensive Validation Test Runner for FQCN Converter.

This script runs all comprehensive validation tests including end-to-end workflows,
regression testing, performance benchmarking, coverage analysis, and GitHub workflow validation.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse


class ComprehensiveTestRunner:
    """Runner for comprehensive validation tests."""
    
    def __init__(self, verbose: bool = False, output_dir: Path = None):
        self.verbose = verbose
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive validation tests."""
        print("🚀 Starting Comprehensive Validation Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test suites to run
        test_suites = [
            ("End-to-End Workflow Validation", self.run_end_to_end_tests),
            ("Regression and Performance Testing", self.run_regression_tests),
            ("Test Coverage and Quality Reporting", self.run_coverage_tests),
            ("GitHub Workflow Testing", self.run_workflow_tests),
            ("Integration Test Suite", self.run_integration_tests),
            ("Unit Test Suite", self.run_unit_tests),
            ("Performance Benchmarks", self.run_performance_benchmarks)
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n📋 Running {suite_name}...")
            print("-" * 40)
            
            suite_start = time.time()
            
            try:
                result = test_function()
                suite_duration = time.time() - suite_start
                
                self.results[suite_name] = {
                    'status': 'PASSED' if result['success'] else 'FAILED',
                    'duration': suite_duration,
                    'details': result
                }
                
                status_emoji = "✅" if result['success'] else "❌"
                print(f"{status_emoji} {suite_name}: {self.results[suite_name]['status']} ({suite_duration:.2f}s)")
                
                if not result['success'] and self.verbose:
                    print(f"   Errors: {result.get('errors', [])}")
                
            except Exception as e:
                suite_duration = time.time() - suite_start
                self.results[suite_name] = {
                    'status': 'ERROR',
                    'duration': suite_duration,
                    'error': str(e)
                }
                
                print(f"💥 {suite_name}: ERROR ({suite_duration:.2f}s)")
                if self.verbose:
                    print(f"   Exception: {str(e)}")
        
        total_duration = time.time() - start_time
        
        # Generate summary
        self.generate_summary_report(total_duration)
        
        return self.results
    
    def run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run end-to-end workflow validation tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_end_to_end_workflow_validation.py",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """Run regression and performance tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_regression_and_performance.py",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_coverage_tests(self) -> Dict[str, Any]:
        """Run coverage and quality reporting tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_coverage_and_quality_reporting.py",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_workflow_tests(self) -> Dict[str, Any]:
        """Run GitHub workflow validation tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/test_github_workflow_validation.py",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v", "--tb=short",
            "--ignore=tests/integration/test_end_to_end_workflow_validation.py",
            "--ignore=tests/integration/test_regression_and_performance.py",
            "--ignore=tests/integration/test_coverage_and_quality_reporting.py",
            "--ignore=tests/integration/test_github_workflow_validation.py"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run all unit tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmark tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v", "--tb=short"
        ]
        
        if self.verbose:
            cmd.extend(["--capture=no"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_with_coverage(self) -> Dict[str, Any]:
        """Run tests with coverage analysis."""
        print("\n📊 Running Tests with Coverage Analysis...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=src/fqcn_converter",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "tests/",
            "-v"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Move coverage reports to output directory
        coverage_files = [
            "htmlcov",
            "coverage.xml",
            ".coverage"
        ]
        
        for coverage_file in coverage_files:
            if Path(coverage_file).exists():
                if Path(coverage_file).is_dir():
                    import shutil
                    shutil.move(coverage_file, self.output_dir / coverage_file)
                else:
                    Path(coverage_file).rename(self.output_dir / coverage_file)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    def run_quality_checks(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("\n🔍 Running Code Quality Checks...")
        
        quality_results = {}
        
        # Flake8 linting
        flake8_result = subprocess.run([
            sys.executable, "-m", "flake8",
            "src", "tests", "scripts",
            "--count", "--statistics"
        ], capture_output=True, text=True)
        
        quality_results['flake8'] = {
            'success': flake8_result.returncode == 0,
            'output': flake8_result.stdout + flake8_result.stderr
        }
        
        # Black formatting check
        black_result = subprocess.run([
            sys.executable, "-m", "black",
            "--check", "--diff",
            "src", "tests", "scripts"
        ], capture_output=True, text=True)
        
        quality_results['black'] = {
            'success': black_result.returncode == 0,
            'output': black_result.stdout + black_result.stderr
        }
        
        # MyPy type checking
        mypy_result = subprocess.run([
            sys.executable, "-m", "mypy",
            "src"
        ], capture_output=True, text=True)
        
        quality_results['mypy'] = {
            'success': mypy_result.returncode == 0,
            'output': mypy_result.stdout + mypy_result.stderr
        }
        
        # Bandit security scan
        bandit_result = subprocess.run([
            sys.executable, "-m", "bandit",
            "-r", "src",
            "-f", "txt"
        ], capture_output=True, text=True)
        
        quality_results['bandit'] = {
            'success': bandit_result.returncode == 0,
            'output': bandit_result.stdout + bandit_result.stderr
        }
        
        overall_success = all(result['success'] for result in quality_results.values())
        
        return {
            'success': overall_success,
            'details': quality_results
        }
    
    def generate_summary_report(self, total_duration: float):
        """Generate comprehensive summary report."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 60)
        
        # Count results
        passed = sum(1 for result in self.results.values() if result['status'] == 'PASSED')
        failed = sum(1 for result in self.results.values() if result['status'] == 'FAILED')
        errors = sum(1 for result in self.results.values() if result['status'] == 'ERROR')
        total = len(self.results)
        
        print(f"Total Test Suites: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        
        # Success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        print("-" * 40)
        
        for suite_name, result in self.results.items():
            status_emoji = {
                'PASSED': '✅',
                'FAILED': '❌',
                'ERROR': '💥'
            }.get(result['status'], '❓')
            
            print(f"{status_emoji} {suite_name}: {result['status']} ({result['duration']:.2f}s)")
        
        # Generate JSON report
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration': total_duration,
            'summary': {
                'total_suites': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'success_rate': success_rate
            },
            'results': self.results
        }
        
        report_file = self.output_dir / "comprehensive_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Overall status
        if failed == 0 and errors == 0:
            print(f"\n🎉 ALL VALIDATION TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  VALIDATION ISSUES DETECTED!")
            print(f"   Please review failed tests and address issues.")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive validation tests")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("test_results"),
        help="Output directory for test results"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage analysis"
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Run code quality checks"
    )
    parser.add_argument(
        "--suite",
        choices=[
            "end-to-end", "regression", "coverage", "workflows",
            "integration", "unit", "performance", "all"
        ],
        default="all",
        help="Specific test suite to run"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = ComprehensiveTestRunner(
        verbose=args.verbose,
        output_dir=args.output_dir
    )
    
    try:
        if args.suite == "all":
            # Run all tests
            results = runner.run_all_tests()
            
            # Run coverage if requested
            if args.coverage:
                coverage_result = runner.run_with_coverage()
                results["Coverage Analysis"] = {
                    'status': 'PASSED' if coverage_result['success'] else 'FAILED',
                    'details': coverage_result
                }
            
            # Run quality checks if requested
            if args.quality:
                quality_result = runner.run_quality_checks()
                results["Quality Checks"] = {
                    'status': 'PASSED' if quality_result['success'] else 'FAILED',
                    'details': quality_result
                }
        
        else:
            # Run specific suite
            suite_methods = {
                "end-to-end": runner.run_end_to_end_tests,
                "regression": runner.run_regression_tests,
                "coverage": runner.run_coverage_tests,
                "workflows": runner.run_workflow_tests,
                "integration": runner.run_integration_tests,
                "unit": runner.run_unit_tests,
                "performance": runner.run_performance_benchmarks
            }
            
            if args.suite in suite_methods:
                print(f"🚀 Running {args.suite} test suite...")
                result = suite_methods[args.suite]()
                
                if result['success']:
                    print(f"✅ {args.suite} tests PASSED")
                    sys.exit(0)
                else:
                    print(f"❌ {args.suite} tests FAILED")
                    if args.verbose:
                        print(result['stderr'])
                    sys.exit(1)
        
        # Determine overall success
        overall_success = runner.generate_summary_report(0)
        
        if overall_success:
            print(f"\n🎉 Comprehensive validation completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Comprehensive validation failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n💥 Unexpected error during test execution: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()