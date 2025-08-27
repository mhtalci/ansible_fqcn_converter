#!/usr/bin/env python3
"""
Performance test runner with baseline establishment and reporting.

This script runs performance tests, establishes baselines if needed,
and generates comprehensive performance reports.
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))


def run_performance_tests(establish_baselines=False, generate_reports=True, 
                         test_pattern="test_performance", output_dir=None):
    """Run performance tests with optional baseline establishment and reporting."""
    
    if output_dir is None:
        output_dir = Path("test_reports/performance")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Running Performance Tests")
    print("=" * 50)
    
    # Step 1: Establish baselines if requested
    if establish_baselines:
        print("\n📊 Establishing Performance Baselines...")
        try:
            from scripts.performance_baseline_setup import main as baseline_main
            sys.argv = ["performance_baseline_setup.py", "--establish-baselines", 
                       "--output-dir", str(output_dir)]
            baseline_main()
            print("✓ Baselines established successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not establish baselines: {e}")
    
    # Step 2: Run performance tests
    print(f"\n🧪 Running Performance Tests (pattern: {test_pattern})...")
    
    # Build pytest command
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "-m", "performance",
        f"tests/performance/{test_pattern}*",
        "--tb=short",
        "--durations=10",
        f"--junitxml={output_dir}/performance_junit.xml"
    ]
    
    try:
        result = subprocess.run(pytest_cmd, capture_output=True, text=True)
        
        print(f"Test execution completed with exit code: {result.returncode}")
        
        if result.stdout:
            print("\nTest Output:")
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print("\nTest Errors:")
            print(result.stderr)
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1
    
    # Step 3: Generate performance reports
    if generate_reports:
        print("\n📈 Generating Performance Reports...")
        try:
            from tests.fixtures.performance_reporter import PerformanceReporter
            from tests.fixtures.performance_baselines import PerformanceBaselineManager
            
            # Generate comprehensive report
            manager = PerformanceBaselineManager()
            reporter = PerformanceReporter(manager)
            reporter.report_dir = output_dir
            
            comprehensive_report = reporter.generate_comprehensive_report()
            trend_report = reporter.generate_trend_report()
            
            # Save trend report
            import json
            trend_file = output_dir / "performance_trends.json"
            with open(trend_file, 'w') as f:
                json.dump(trend_report, f, indent=2)
            
            print("✓ Performance reports generated successfully")
            print(f"  📁 Report directory: {output_dir}")
            print(f"  📊 Comprehensive report: performance_report_*.json/html")
            print(f"  📈 Trend report: {trend_file}")
            
            # Print summary
            summary = comprehensive_report.get("summary", {})
            print(f"\n📋 Performance Summary:")
            print(f"  • Total baselines: {summary.get('total_baselines', 0)}")
            print(f"  • Total measurements: {summary.get('total_measurements', 0)}")
            print(f"  • Operations tracked: {summary.get('operations_tracked', 0)}")
            
            # Print recommendations if any
            recommendations = comprehensive_report.get("recommendations", [])
            if recommendations:
                print(f"\n⚠️  Performance Recommendations ({len(recommendations)}):")
                for rec in recommendations[:3]:  # Show first 3
                    print(f"  • {rec['description']} ({rec['priority']} priority)")
                if len(recommendations) > 3:
                    print(f"  • ... and {len(recommendations) - 3} more (see full report)")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not generate reports: {e}")
    
    print(f"\n✅ Performance testing completed!")
    return result.returncode if 'result' in locals() else 0


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run performance tests with monitoring")
    parser.add_argument("--establish-baselines", action="store_true",
                       help="Establish new performance baselines before testing")
    parser.add_argument("--no-reports", action="store_true",
                       help="Skip generating performance reports")
    parser.add_argument("--test-pattern", default="test_performance",
                       help="Pattern for test files to run (default: test_performance)")
    parser.add_argument("--output-dir", type=Path, default=Path("test_reports/performance"),
                       help="Output directory for reports")
    
    args = parser.parse_args()
    
    return run_performance_tests(
        establish_baselines=args.establish_baselines,
        generate_reports=not args.no_reports,
        test_pattern=args.test_pattern,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    sys.exit(main())