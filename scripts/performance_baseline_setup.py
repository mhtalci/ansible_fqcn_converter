#!/usr/bin/env python3
"""
Performance baseline setup script.

This script establishes performance baselines for the FQCN Converter
and generates initial performance reports.
"""

import sys
import argparse
from pathlib import Path

# Add src and tests to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "tests"))
sys.path.insert(0, str(project_root))

try:
    from tests.fixtures.performance_utils import PerformanceUtils
    from tests.fixtures.performance_baselines import PerformanceBaselineManager
    from tests.fixtures.performance_reporter import PerformanceReporter
    from tests.fixtures.performance_monitor import get_performance_monitor
except ImportError as e:
    print(f"Error importing performance modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def main():
    """Main function to set up performance baselines."""
    parser = argparse.ArgumentParser(description="Set up performance baselines")
    parser.add_argument("--establish-baselines", action="store_true",
                       help="Establish new performance baselines")
    parser.add_argument("--generate-report", action="store_true",
                       help="Generate performance report")
    parser.add_argument("--output-dir", type=Path, default=Path("test_reports/performance"),
                       help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.establish_baselines:
        print("Establishing performance baselines...")
        try:
            PerformanceUtils.establish_performance_baselines()
            print("✓ Performance baselines established successfully")
        except Exception as e:
            print(f"✗ Error establishing baselines: {e}")
            return 1
    
    if args.generate_report:
        print("Generating performance report...")
        try:
            reporter = PerformanceReporter()
            report = reporter.generate_comprehensive_report()
            
            # Also generate trend report
            trend_report = reporter.generate_trend_report()
            
            trend_file = args.output_dir / "performance_trends.json"
            import json
            with open(trend_file, 'w') as f:
                json.dump(trend_report, f, indent=2)
            
            print(f"✓ Performance reports generated in {args.output_dir}")
            print(f"  - Comprehensive report: performance_report_*.json/html")
            print(f"  - Trend report: {trend_file}")
            
        except Exception as e:
            print(f"✗ Error generating report: {e}")
            return 1
    
    if not args.establish_baselines and not args.generate_report:
        print("No action specified. Use --establish-baselines or --generate-report")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())