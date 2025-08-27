#!/usr/bin/env python3
"""
Comprehensive Test Execution with Enhanced Reporting

This script provides complete test execution with:
- Multiple output formats (JUnit XML, LCOV, HTML, JSON)
- Detailed coverage analysis with actionable insights
- Performance metrics tracking and trend analysis
- CI/CD compatible reporting for all major platforms
- Interactive dashboards and executive summaries
"""

import argparse
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.enhanced_test_reporter import EnhancedTestReporter


class ComprehensiveTestRunner:
    """Comprehensive test runner with enhanced reporting capabilities."""
    
    def __init__(self, output_dir: str = "test_reports"):
        """Initialize the comprehensive test runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.reporter = EnhancedTestReporter(str(self.output_dir))
        
    def run_tests_with_comprehensive_reporting(self,
                                             test_mode: str = "sequential",
                                             workers: Optional[int] = None,
                                             markers: Optional[str] = None,
                                             test_path: Optional[str] = None,
                                             coverage_threshold: float = 85.0,
                                             config_file: str = "pytest-reporting.ini") -> Dict[str, Any]:
        """
        Run tests with comprehensive reporting and analysis.
        
        Args:
            test_mode: Test execution mode ("sequential" or "parallel")
            workers: Number of workers for parallel execution
            markers: Test markers to select
            test_path: Specific test path to run
            coverage_threshold: Minimum coverage threshold
            config_file: Pytest configuration file to use
            
        Returns:
            Dictionary containing all test results and report paths
        """
        print(f"🚀 Starting comprehensive test execution with enhanced reporting...")
        print(f"   Mode: {test_mode}")
        print(f"   Coverage Threshold: {coverage_threshold}%")
        print(f"   Config: {config_file}")
        
        # Prepare test environment
        self._prepare_test_environment()
        
        # Build and execute pytest command
        start_time = time.time()
        cmd = self._build_comprehensive_pytest_command(
            test_mode, workers, markers, test_path, coverage_threshold, config_file
        )
        
        print(f"📋 Executing: {' '.join(cmd[:10])}...")  # Show first 10 args
        
        # Execute tests
        result = self._execute_tests_with_monitoring(cmd)
        execution_time = time.time() - start_time
        
        # Generate comprehensive reports
        print("📊 Generating comprehensive reports...")
        report_manifest = self.reporter.generate_comprehensive_reports()
        
        # Generate additional CI/CD artifacts
        ci_artifacts = self._generate_ci_cd_artifacts(result, execution_time)
        
        # Create test execution summary
        execution_summary = {
            "execution_time": execution_time,
            "command": cmd,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "report_manifest": report_manifest,
            "ci_artifacts": ci_artifacts,
            "output_directory": str(self.output_dir)
        }
        
        # Print summary
        self._print_execution_summary(execution_summary)
        
        return execution_summary
    
    def _prepare_test_environment(self):
        """Prepare the test environment for comprehensive reporting."""
        # Ensure all report directories exist
        subdirs = [
            "coverage", "performance", "junit", "trends", "logs", 
            "artifacts", "screenshots", "profiles", "insights",
            "ci_reports", "quality_metrics", "dashboards"
        ]
        
        for subdir in subdirs:
            (self.output_dir / subdir).mkdir(exist_ok=True)
        
        # Clean previous run data if needed
        self._clean_previous_reports()
        
        print("✅ Test environment prepared")
    
    def _clean_previous_reports(self):
        """Clean previous test reports to avoid conflicts."""
        # Remove old coverage data
        coverage_file = Path(".coverage")
        if coverage_file.exists():
            coverage_file.unlink()
        
        # Clean pytest cache
        cache_dir = Path(".pytest_cache")
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
    
    def _build_comprehensive_pytest_command(self,
                                          test_mode: str,
                                          workers: Optional[int],
                                          markers: Optional[str],
                                          test_path: Optional[str],
                                          coverage_threshold: float,
                                          config_file: str) -> List[str]:
        """Build comprehensive pytest command with all reporting options."""
        cmd = ["python", "-m", "pytest"]
        
        # Configuration file
        cmd.extend(["-c", config_file])
        
        # Parallel execution setup
        if test_mode == "parallel":
            if workers:
                cmd.extend(["--numprocesses", str(workers)])
            else:
                cmd.extend(["--numprocesses", "auto"])
            cmd.extend(["--dist", "loadscope"])
        
        # Coverage options with comprehensive reporting
        cmd.extend([
            "--cov=src/fqcn_converter",
            "--cov-config=.coveragerc-comprehensive",
            "--cov-report=term-missing:skip-covered",
            f"--cov-report=html:{self.output_dir}/coverage/html",
            f"--cov-report=xml:{self.output_dir}/coverage/coverage.xml",
            f"--cov-report=json:{self.output_dir}/coverage/coverage.json",
            f"--cov-report=lcov:{self.output_dir}/coverage/coverage.lcov",
            "--cov-branch",
            "--cov-context=test",
            f"--cov-fail-under={coverage_threshold}"
        ])
        
        # Enhanced JUnit XML with detailed metadata
        timestamp = self.reporter.timestamp
        cmd.extend([
            f"--junit-xml={self.output_dir}/junit/junit_{timestamp}.xml",
            "--junit-logging=all",
            "--junit-log-passing-tests=true",
            "--junit-duration-report=total",
            "--junit-family=xunit2",
            "--junit-suite-name=fqcn_converter_comprehensive"
        ])
        
        # Performance and timing analysis
        cmd.extend([
            "--durations=0",  # Show all test durations
            "--durations-min=0.01",  # Show tests slower than 10ms
            "--tb=short",
            "--verbose",
            "--showlocals"
        ])
        
        # Additional logging and debugging
        cmd.extend([
            f"--resultlog={self.output_dir}/logs/pytest_results_{timestamp}.log",
            "--capture=no" if os.getenv("DEBUG") else "--capture=sys"
        ])
        
        # Test selection
        if markers:
            cmd.extend(["-m", markers])
        
        if test_path:
            cmd.append(test_path)
        
        return cmd
    
    def _execute_tests_with_monitoring(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute tests with resource monitoring."""
        try:
            # Start resource monitoring if available
            monitor_process = self._start_resource_monitoring()
            
            # Execute tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                cwd=project_root
            )
            
            # Stop resource monitoring
            if monitor_process:
                self._stop_resource_monitoring(monitor_process)
            
            # Save execution output
            self._save_execution_output(result)
            
            return result
            
        except subprocess.TimeoutExpired:
            print("❌ Test execution timed out after 30 minutes")
            raise
        except Exception as e:
            print(f"❌ Error executing tests: {e}")
            raise
    
    def _start_resource_monitoring(self) -> Optional[subprocess.Popen]:
        """Start resource monitoring during test execution."""
        try:
            # Try to start system resource monitoring
            import psutil
            # This would start a background process to monitor CPU, memory, etc.
            return None  # Placeholder for actual monitoring process
        except ImportError:
            return None
    
    def _stop_resource_monitoring(self, monitor_process: Optional[subprocess.Popen]):
        """Stop resource monitoring and collect data."""
        if monitor_process:
            monitor_process.terminate()
            # Collect and save monitoring data
    
    def _save_execution_output(self, result: subprocess.CompletedProcess):
        """Save test execution output for analysis."""
        timestamp = self.reporter.timestamp
        
        # Save stdout
        stdout_path = self.output_dir / "logs" / f"pytest_stdout_{timestamp}.log"
        with open(stdout_path, 'w') as f:
            f.write(result.stdout)
        
        # Save stderr
        stderr_path = self.output_dir / "logs" / f"pytest_stderr_{timestamp}.log"
        with open(stderr_path, 'w') as f:
            f.write(result.stderr)
        
        # Save combined output
        combined_path = self.output_dir / "logs" / f"pytest_combined_{timestamp}.log"
        with open(combined_path, 'w') as f:
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
    
    def _generate_ci_cd_artifacts(self, result: subprocess.CompletedProcess, 
                                execution_time: float) -> Dict[str, Any]:
        """Generate CI/CD specific artifacts and outputs."""
        artifacts = {
            "github_actions": self._generate_github_actions_artifacts(result, execution_time),
            "gitlab_ci": self._generate_gitlab_ci_artifacts(result, execution_time),
            "jenkins": self._generate_jenkins_artifacts(result, execution_time),
            "azure_devops": self._generate_azure_devops_artifacts(result, execution_time)
        }
        
        return artifacts
    
    def _generate_github_actions_artifacts(self, result: subprocess.CompletedProcess, 
                                         execution_time: float) -> Dict[str, Any]:
        """Generate GitHub Actions specific artifacts."""
        github_dir = self.output_dir / "ci_reports" / "github_actions"
        github_dir.mkdir(exist_ok=True)
        
        # Generate job summary
        summary = self._create_github_job_summary(result, execution_time)
        with open(github_dir / "job_summary.md", 'w') as f:
            f.write(summary)
        
        # Generate step outputs
        outputs = {
            "test_result": "success" if result.returncode == 0 else "failure",
            "execution_time": f"{execution_time:.2f}",
            "coverage_report": "test_reports/coverage/html/index.html",
            "junit_report": f"test_reports/junit/junit_{self.reporter.timestamp}.xml"
        }
        
        with open(github_dir / "step_outputs.json", 'w') as f:
            import json
            json.dump(outputs, f, indent=2)
        
        return {
            "job_summary": str(github_dir / "job_summary.md"),
            "step_outputs": str(github_dir / "step_outputs.json"),
            "artifacts": [
                "test_reports/coverage/html/",
                f"test_reports/junit/junit_{self.reporter.timestamp}.xml"
            ]
        }
    
    def _create_github_job_summary(self, result: subprocess.CompletedProcess, 
                                 execution_time: float) -> str:
        """Create GitHub Actions job summary."""
        status_emoji = "✅" if result.returncode == 0 else "❌"
        status_text = "Passed" if result.returncode == 0 else "Failed"
        
        summary = f"""# Test Execution Summary {status_emoji}

## Results
- **Status**: {status_text}
- **Execution Time**: {execution_time:.2f} seconds
- **Exit Code**: {result.returncode}

## Reports Generated
- 📊 [HTML Coverage Report](coverage/html/index.html)
- 📋 [JUnit XML Report](junit/junit_{self.reporter.timestamp}.xml)
- 📈 [Performance Analysis](performance/performance_report_{self.reporter.timestamp}.md)
- 🎯 [Insights Dashboard](dashboards/insights_{self.reporter.timestamp}.html)

## Quick Links
- [Detailed Coverage Analysis](insights/coverage_analysis_{self.reporter.timestamp}.json)
- [Executive Summary](executive_summary_{self.reporter.timestamp}.md)

---
*Generated by Comprehensive Test Reporter*
"""
        return summary
    
    def _generate_gitlab_ci_artifacts(self, result: subprocess.CompletedProcess, 
                                    execution_time: float) -> Dict[str, Any]:
        """Generate GitLab CI specific artifacts."""
        gitlab_dir = self.output_dir / "ci_reports" / "gitlab_ci"
        gitlab_dir.mkdir(exist_ok=True)
        
        # Generate coverage report for GitLab
        coverage_report = {
            "coverage": 0.0,  # This would be extracted from actual coverage data
            "format": "cobertura",
            "file": f"test_reports/coverage/coverage.xml"
        }
        
        with open(gitlab_dir / "coverage_report.json", 'w') as f:
            import json
            json.dump(coverage_report, f, indent=2)
        
        return {
            "coverage_report": str(gitlab_dir / "coverage_report.json"),
            "test_report": f"test_reports/junit/junit_{self.reporter.timestamp}.xml"
        }
    
    def _generate_jenkins_artifacts(self, result: subprocess.CompletedProcess, 
                                  execution_time: float) -> Dict[str, Any]:
        """Generate Jenkins specific artifacts."""
        jenkins_dir = self.output_dir / "ci_reports" / "jenkins"
        jenkins_dir.mkdir(exist_ok=True)
        
        # Jenkins typically uses JUnit XML and HTML reports
        return {
            "junit_xml": f"test_reports/junit/junit_{self.reporter.timestamp}.xml",
            "html_report": "test_reports/coverage/html/index.html",
            "build_status": "SUCCESS" if result.returncode == 0 else "FAILURE"
        }
    
    def _generate_azure_devops_artifacts(self, result: subprocess.CompletedProcess, 
                                       execution_time: float) -> Dict[str, Any]:
        """Generate Azure DevOps specific artifacts."""
        azure_dir = self.output_dir / "ci_reports" / "azure_devops"
        azure_dir.mkdir(exist_ok=True)
        
        return {
            "test_results": f"test_reports/junit/junit_{self.reporter.timestamp}.xml",
            "code_coverage": "test_reports/coverage/coverage.xml",
            "build_result": "Succeeded" if result.returncode == 0 else "Failed"
        }
    
    def _print_execution_summary(self, summary: Dict[str, Any]):
        """Print comprehensive execution summary."""
        print(f"\n{'='*80}")
        print("🎯 COMPREHENSIVE TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        
        # Execution results
        status_emoji = "✅" if summary["success"] else "❌"
        print(f"📊 Execution Status: {status_emoji} {'SUCCESS' if summary['success'] else 'FAILURE'}")
        print(f"⏱️  Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"🔢 Exit Code: {summary['exit_code']}")
        
        # Report locations
        print(f"\n📁 Reports Generated:")
        print(f"   📊 Coverage Reports: {summary['output_directory']}/coverage/")
        print(f"   📋 JUnit XML: {summary['output_directory']}/junit/")
        print(f"   📈 Performance: {summary['output_directory']}/performance/")
        print(f"   🎯 Insights: {summary['output_directory']}/insights/")
        print(f"   📱 Dashboard: {summary['output_directory']}/dashboards/")
        
        # CI/CD artifacts
        print(f"\n🔧 CI/CD Artifacts:")
        for platform, artifacts in summary["ci_artifacts"].items():
            if artifacts:
                print(f"   {platform.replace('_', ' ').title()}: ✅")
        
        # Quick actions
        print(f"\n🚀 Quick Actions:")
        print(f"   View Coverage: open {summary['output_directory']}/coverage/html/index.html")
        print(f"   View Dashboard: open {summary['output_directory']}/dashboards/insights_{self.reporter.timestamp}.html")
        print(f"   View Summary: cat {summary['output_directory']}/executive_summary_{self.reporter.timestamp}.md")
        
        print(f"{'='*80}")


def main():
    """Main entry point for comprehensive test execution with enhanced reporting."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Execution with Enhanced Reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with comprehensive reporting
  python scripts/run_comprehensive_reporting_tests.py
  
  # Run tests in parallel with enhanced insights
  python scripts/run_comprehensive_reporting_tests.py --mode parallel --workers 4
  
  # Run specific test suite with detailed analysis
  python scripts/run_comprehensive_reporting_tests.py --markers unit --coverage-threshold 95
  
  # Generate reports for CI/CD pipeline
  python scripts/run_comprehensive_reporting_tests.py --mode parallel --ci-optimized
  
  # Quick validation with fast tests only
  python scripts/run_comprehensive_reporting_tests.py --markers "fast and unit" --mode parallel
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
        help="Test markers to select (e.g., 'unit', 'integration', 'fast and unit')"
    )
    
    parser.add_argument(
        "--test-path", 
        help="Specific test path to run (e.g., 'tests/unit')"
    )
    
    parser.add_argument(
        "--coverage-threshold", 
        type=float, 
        default=85.0,
        help="Minimum coverage threshold percentage (default: 85.0)"
    )
    
    parser.add_argument(
        "--config", 
        default="pytest-reporting.ini",
        help="Pytest configuration file (default: pytest-reporting.ini)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="test_reports",
        help="Output directory for reports (default: test_reports)"
    )
    
    parser.add_argument(
        "--ci-optimized", 
        action="store_true",
        help="Optimize for CI/CD execution (faster, essential reports only)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    
    args = parser.parse_args()
    
    # Set debug environment
    if args.debug:
        os.environ["DEBUG"] = "1"
    
    # Adjust settings for CI optimization
    if args.ci_optimized:
        if not args.markers:
            args.markers = "not slow"
        args.mode = "parallel"
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Initialize comprehensive test runner
    runner = ComprehensiveTestRunner(args.output_dir)
    
    # Run tests with comprehensive reporting
    try:
        summary = runner.run_tests_with_comprehensive_reporting(
            test_mode=args.mode,
            workers=args.workers,
            markers=args.markers,
            test_path=args.test_path,
            coverage_threshold=args.coverage_threshold,
            config_file=args.config
        )
        
        return 0 if summary["success"] else 1
        
    except Exception as e:
        print(f"❌ Error during comprehensive test execution: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())