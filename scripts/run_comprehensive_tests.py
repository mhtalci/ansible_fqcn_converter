#!/usr/bin/env python3
"""
Comprehensive Test Execution Script with Enhanced Reporting

This script provides a complete test execution framework with:
- Detailed coverage analysis
- Performance metrics tracking
- CI/CD compatible reporting
- Trend analysis
- Actionable insights generation
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.test_reporter import TestReporter


def setup_test_environment():
    """Set up the test environment and create necessary directories."""
    # Create test reports directory structure
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    subdirs = [
        "coverage", "performance", "junit", "trends", "logs", 
        "artifacts", "screenshots", "profiles"
    ]
    
    for subdir in subdirs:
        (reports_dir / subdir).mkdir(exist_ok=True)
    
    # Ensure coverage data directory exists
    (reports_dir / "coverage").mkdir(exist_ok=True)
    
    print(f"Test environment set up in: {reports_dir.absolute()}")


def validate_test_dependencies():
    """Validate that all required test dependencies are available."""
    required_packages = [
        ("pytest", "pytest"),
        ("pytest_cov", "pytest-cov"),
        ("pytest_mock", "pytest-mock"),
        ("xdist", "pytest-xdist"),
        ("coverage", "coverage")
    ]
    
    missing_packages = []
    
    for package_name, pip_name in required_packages:
        try:
            __import__(package_name)
            print(f"✓ {pip_name} is available")
        except ImportError:
            missing_packages.append(pip_name)
            print(f"✗ {pip_name} is missing")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All test dependencies are available")
    return True


def run_comprehensive_test_suite(
    mode: str = "sequential",
    workers: Optional[int] = None,
    markers: Optional[str] = None,
    test_path: Optional[str] = None,
    coverage_threshold: float = 90.0,
    performance_baseline: bool = False,
    generate_artifacts: bool = True
) -> bool:
    """
    Run the comprehensive test suite with full reporting.
    
    Args:
        mode: Test execution mode ("sequential" or "parallel")
        workers: Number of workers for parallel execution
        markers: Test markers to select
        test_path: Specific test path to run
        coverage_threshold: Minimum coverage threshold
        performance_baseline: Whether to establish performance baselines
        generate_artifacts: Whether to generate test artifacts
    
    Returns:
        True if all tests passed and coverage threshold met, False otherwise
    """
    print(f"Starting comprehensive test execution in {mode} mode...")
    
    # Set up environment
    setup_test_environment()
    
    # Validate dependencies
    if not validate_test_dependencies():
        return False
    
    # Initialize comprehensive reporter
    reporter = TestReporter("test_reports")
    
    try:
        # Run tests with comprehensive reporting
        start_time = time.time()
        
        result = reporter.run_tests_with_reporting(
            test_mode=mode,
            workers=workers,
            markers=markers,
            test_path=test_path
        )
        
        total_time = time.time() - start_time
        
        # Print comprehensive summary
        print_test_summary(result, total_time, coverage_threshold)
        
        # Generate additional artifacts if requested
        if generate_artifacts:
            generate_test_artifacts(result, reporter)
        
        # Establish performance baselines if requested
        if performance_baseline:
            establish_performance_baselines(result)
        
        # Determine overall success
        success = (
            result.failed == 0 and 
            result.errors == 0 and 
            result.coverage_percentage >= coverage_threshold
        )
        
        if success:
            print("\n🎉 All tests passed and coverage threshold met!")
        else:
            print(f"\n❌ Test execution failed or coverage below {coverage_threshold}%")
        
        return success
        
    except Exception as e:
        print(f"Error during comprehensive test execution: {e}")
        return False


def print_test_summary(result, total_time: float, coverage_threshold: float):
    """Print a comprehensive test execution summary."""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST EXECUTION SUMMARY")
    print(f"{'='*80}")
    
    # Test results
    print(f"📊 Test Results:")
    print(f"   Total Tests: {result.total_tests}")
    print(f"   Passed:      {result.passed} ({result.passed/result.total_tests*100:.1f}%)")
    print(f"   Failed:      {result.failed} ({result.failed/result.total_tests*100:.1f}%)")
    print(f"   Skipped:     {result.skipped} ({result.skipped/result.total_tests*100:.1f}%)")
    print(f"   Errors:      {result.errors} ({result.errors/result.total_tests*100:.1f}%)")
    
    # Coverage analysis
    coverage_status = "✅" if result.coverage_percentage >= coverage_threshold else "❌"
    print(f"\n📈 Coverage Analysis:")
    print(f"   Coverage:    {result.coverage_percentage:.2f}% {coverage_status}")
    print(f"   Threshold:   {coverage_threshold}%")
    print(f"   Status:      {'PASS' if result.coverage_percentage >= coverage_threshold else 'FAIL'}")
    
    # Performance metrics
    tests_per_second = result.total_tests / result.execution_time if result.execution_time > 0 else 0
    perf_status = "✅" if tests_per_second > 5 else "⚠️" if tests_per_second > 2 else "❌"
    
    print(f"\n⚡ Performance Metrics:")
    print(f"   Execution Time:    {result.execution_time:.2f}s")
    print(f"   Total Time:        {total_time:.2f}s")
    print(f"   Tests/Second:      {tests_per_second:.2f} {perf_status}")
    print(f"   Workers:           {result.worker_count}")
    print(f"   Mode:              {result.test_mode}")
    
    # Failed tests details
    if result.failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in result.failed_tests[:10]:  # Show first 10
            print(f"   - {test}")
        if len(result.failed_tests) > 10:
            print(f"   ... and {len(result.failed_tests) - 10} more")
    
    # Slow tests
    if result.slow_tests:
        print(f"\n🐌 Slowest Tests:")
        for test, duration in sorted(result.slow_tests, key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {test}: {duration:.2f}s")
    
    print(f"\n📁 Reports Location: test_reports/")
    print(f"{'='*80}")


def generate_test_artifacts(result, reporter):
    """Generate additional test artifacts and documentation."""
    print("\nGenerating additional test artifacts...")
    
    artifacts_dir = Path("test_reports/artifacts")
    
    # Generate test execution badge
    generate_test_badge(result, artifacts_dir)
    
    # Generate coverage badge
    generate_coverage_badge(result, artifacts_dir)
    
    # Generate README with test results
    generate_test_readme(result, artifacts_dir)
    
    print("✓ Test artifacts generated")


def generate_test_badge(result, artifacts_dir: Path):
    """Generate a test status badge."""
    if result.failed == 0 and result.errors == 0:
        badge_color = "brightgreen"
        badge_text = f"{result.passed} passing"
    else:
        badge_color = "red"
        badge_text = f"{result.failed + result.errors} failing"
    
    badge_url = f"https://img.shields.io/badge/tests-{badge_text.replace(' ', '%20')}-{badge_color}"
    
    badge_file = artifacts_dir / "test_badge.md"
    with open(badge_file, 'w') as f:
        f.write(f"![Test Status]({badge_url})\n")


def generate_coverage_badge(result, artifacts_dir: Path):
    """Generate a coverage badge."""
    coverage = result.coverage_percentage
    
    if coverage >= 95:
        color = "brightgreen"
    elif coverage >= 90:
        color = "green"
    elif coverage >= 80:
        color = "yellow"
    elif coverage >= 70:
        color = "orange"
    else:
        color = "red"
    
    badge_url = f"https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color}"
    
    badge_file = artifacts_dir / "coverage_badge.md"
    with open(badge_file, 'w') as f:
        f.write(f"![Coverage]({badge_url})\n")


def generate_test_readme(result, artifacts_dir: Path):
    """Generate a README with test execution summary."""
    readme_content = f"""# Test Execution Summary

## Latest Test Run - {result.timestamp}

### Results Overview
- **Total Tests**: {result.total_tests}
- **Passed**: {result.passed}
- **Failed**: {result.failed}
- **Coverage**: {result.coverage_percentage:.2f}%
- **Execution Time**: {result.execution_time:.2f}s

### Status
- Tests: {'✅ PASSING' if result.failed == 0 and result.errors == 0 else '❌ FAILING'}
- Coverage: {'✅ GOOD' if result.coverage_percentage >= 90 else '⚠️ NEEDS IMPROVEMENT'}

### Quick Links
- [HTML Coverage Report](coverage/html/index.html)
- [JUnit XML Report](junit/junit_{result.timestamp}.xml)
- [Detailed Analysis](test_summary_{result.timestamp}.md)

### Test Categories
- Unit Tests: Fast, isolated component tests
- Integration Tests: Component interaction tests
- Performance Tests: Speed and resource usage tests

### Maintenance
This summary is automatically generated after each test run.
For detailed analysis and trends, see the comprehensive reports.
"""
    
    readme_file = artifacts_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)


def establish_performance_baselines(result):
    """Establish performance baselines for future comparisons."""
    print("\nEstablishing performance baselines...")
    
    baselines_file = Path("test_reports/performance/baselines.json")
    
    import json
    
    baselines = {
        "timestamp": result.timestamp,
        "total_tests": result.total_tests,
        "execution_time": result.execution_time,
        "tests_per_second": result.total_tests / result.execution_time if result.execution_time > 0 else 0,
        "worker_count": result.worker_count,
        "test_mode": result.test_mode,
        "slow_test_threshold": 1.0,
        "performance_targets": {
            "min_tests_per_second": 2.0,
            "max_execution_time": 300.0,
            "max_slow_tests": 10
        }
    }
    
    with open(baselines_file, 'w') as f:
        json.dump(baselines, f, indent=2)
    
    print(f"✓ Performance baselines established: {baselines_file}")


def main():
    """Main entry point for comprehensive test execution."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Execution with Enhanced Reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with comprehensive reporting
  python scripts/run_comprehensive_tests.py
  
  # Run tests in parallel with 4 workers
  python scripts/run_comprehensive_tests.py --mode parallel --workers 4
  
  # Run only unit tests with 95% coverage threshold
  python scripts/run_comprehensive_tests.py --markers unit --coverage-threshold 95
  
  # Run specific test path with performance baselines
  python scripts/run_comprehensive_tests.py --test-path tests/unit --baseline
  
  # Quick validation run
  python scripts/run_comprehensive_tests.py --mode parallel --markers "unit and fast"
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["sequential", "parallel"], 
        default="sequential",
        help="Test execution mode (default: sequential)"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        help="Number of workers for parallel mode (default: auto)"
    )
    
    parser.add_argument(
        "--markers", 
        help="Test markers to select (e.g., 'unit', 'integration', 'unit and fast')"
    )
    
    parser.add_argument(
        "--test-path", 
        help="Specific test path to run (e.g., 'tests/unit')"
    )
    
    parser.add_argument(
        "--coverage-threshold", 
        type=float, 
        default=90.0,
        help="Minimum coverage threshold percentage (default: 90.0)"
    )
    
    parser.add_argument(
        "--baseline", 
        action="store_true",
        help="Establish performance baselines"
    )
    
    parser.add_argument(
        "--no-artifacts", 
        action="store_true",
        help="Skip generating test artifacts"
    )
    
    parser.add_argument(
        "--validate-only", 
        action="store_true",
        help="Only validate test environment, don't run tests"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Validate-only mode
    if args.validate_only:
        setup_test_environment()
        success = validate_test_dependencies()
        print("✓ Test environment validation complete" if success else "❌ Test environment validation failed")
        return 0 if success else 1
    
    # Run comprehensive test suite
    success = run_comprehensive_test_suite(
        mode=args.mode,
        workers=args.workers,
        markers=args.markers,
        test_path=args.test_path,
        coverage_threshold=args.coverage_threshold,
        performance_baseline=args.baseline,
        generate_artifacts=not args.no_artifacts
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())