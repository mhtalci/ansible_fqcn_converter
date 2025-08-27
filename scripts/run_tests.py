#!/usr/bin/env python3
"""
Test execution script with support for different execution modes.

This script provides convenient commands for running tests in various modes:
- Sequential (single-threaded)
- Parallel (multi-worker)
- Performance testing
- Coverage analysis
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return False


def run_sequential_tests(args):
    """Run tests in sequential mode."""
    cmd = [
        "python", "-m", "pytest",
        "-c", "pytest.ini",
        "--verbose",
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src/fqcn_converter",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/sequential",
            "--cov-report=xml:coverage-sequential.xml"
        ])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.test_path:
        cmd.append(args.test_path)
    
    return run_command(cmd, "Sequential Test Execution")


def run_parallel_tests(args):
    """Run tests in parallel mode."""
    cmd = [
        "python", "-m", "pytest",
        "-c", "pytest-parallel.ini",
        "--numprocesses", str(args.workers) if args.workers else "auto",
        "--dist", args.distribution,
    ]
    
    if args.coverage:
        cmd.extend([
            "--cov=src/fqcn_converter",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/parallel",
            "--cov-report=xml:coverage-parallel.xml"
        ])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    if args.test_path:
        cmd.append(args.test_path)
    
    return run_command(cmd, f"Parallel Test Execution ({args.workers or 'auto'} workers)")


def run_performance_tests(args):
    """Run performance tests with appropriate configuration."""
    cmd = [
        "python", "-m", "pytest",
        "-c", "pytest.ini",
        "-m", "performance",
        "--verbose",
        "--durations=0",
    ]
    
    if args.parallel:
        cmd.extend([
            "--numprocesses", "2",  # Limited workers for performance tests
            "--dist", "loadfile"
        ])
    
    return run_command(cmd, "Performance Test Execution")


def run_coverage_analysis(args):
    """Run comprehensive coverage analysis."""
    # First run tests with coverage
    success = run_sequential_tests(args)
    if not success:
        return False
    
    # Generate coverage reports
    coverage_commands = [
        (["coverage", "report", "--show-missing"], "Coverage Report"),
        (["coverage", "html", "-d", "htmlcov/analysis"], "HTML Coverage Report"),
        (["coverage", "xml", "-o", "coverage-analysis.xml"], "XML Coverage Report"),
    ]
    
    for cmd, desc in coverage_commands:
        if not run_command(cmd, desc):
            print(f"Warning: Failed to generate {desc}")
    
    return True


def validate_parallel_setup():
    """Validate that parallel test execution is properly configured."""
    print("Validating parallel test setup...")
    
    # Check if pytest-xdist is installed
    try:
        import xdist
        print(f"✓ pytest-xdist version: {xdist.__version__}")
    except ImportError:
        print("✗ pytest-xdist not installed. Run: pip install pytest-xdist")
        return False
    
    # Check if pytest-forked is installed
    try:
        import pytest_forked
        print(f"✓ pytest-forked available")
    except ImportError:
        print("✗ pytest-forked not installed. Run: pip install pytest-forked")
        return False
    
    # Check configuration files
    config_files = ["pytest.ini", "pytest-parallel.ini"]
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✓ Configuration file: {config_file}")
        else:
            print(f"✗ Missing configuration file: {config_file}")
            return False
    
    print("✓ Parallel test setup validation complete")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run FQCN Converter tests in various modes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests sequentially
  python scripts/run_tests.py sequential
  
  # Run tests in parallel with 4 workers
  python scripts/run_tests.py parallel --workers 4
  
  # Run only unit tests in parallel
  python scripts/run_tests.py parallel --markers "unit"
  
  # Run performance tests
  python scripts/run_tests.py performance
  
  # Run coverage analysis
  python scripts/run_tests.py coverage
  
  # Validate parallel setup
  python scripts/run_tests.py validate
        """
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Test execution mode")
    
    # Sequential mode
    seq_parser = subparsers.add_parser("sequential", help="Run tests sequentially")
    seq_parser.add_argument("--coverage", action="store_true", help="Include coverage analysis")
    seq_parser.add_argument("--markers", help="Test markers to select (e.g., 'unit', 'integration')")
    seq_parser.add_argument("--test-path", help="Specific test path to run")
    
    # Parallel mode
    par_parser = subparsers.add_parser("parallel", help="Run tests in parallel")
    par_parser.add_argument("--workers", type=int, help="Number of workers (default: auto)")
    par_parser.add_argument("--distribution", default="loadscope", 
                           choices=["loadscope", "loadfile", "worksteal"],
                           help="Test distribution strategy")
    par_parser.add_argument("--coverage", action="store_true", help="Include coverage analysis")
    par_parser.add_argument("--markers", help="Test markers to select")
    par_parser.add_argument("--test-path", help="Specific test path to run")
    
    # Performance mode
    perf_parser = subparsers.add_parser("performance", help="Run performance tests")
    perf_parser.add_argument("--parallel", action="store_true", help="Run performance tests in parallel")
    
    # Coverage mode
    cov_parser = subparsers.add_parser("coverage", help="Run comprehensive coverage analysis")
    cov_parser.add_argument("--markers", help="Test markers to select")
    cov_parser.add_argument("--test-path", help="Specific test path to run")
    
    # Validation mode
    subparsers.add_parser("validate", help="Validate parallel test setup")
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return 1
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    success = False
    
    if args.mode == "sequential":
        success = run_sequential_tests(args)
    elif args.mode == "parallel":
        if validate_parallel_setup():
            success = run_parallel_tests(args)
    elif args.mode == "performance":
        success = run_performance_tests(args)
    elif args.mode == "coverage":
        args.coverage = True  # Force coverage for coverage mode
        success = run_coverage_analysis(args)
    elif args.mode == "validate":
        success = validate_parallel_setup()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())