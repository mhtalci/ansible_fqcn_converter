#!/usr/bin/env python3
"""
Comprehensive Test Reporting System for FQCN Converter

This module provides detailed test reporting with actionable insights,
performance metrics tracking, and CI/CD compatible output formats.
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import subprocess
import argparse


@dataclass
class TestExecutionResult:
    """Test execution result tracking."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    coverage_percentage: float
    execution_time: float
    worker_count: int
    test_mode: str
    timestamp: str
    failed_tests: List[str]
    slow_tests: List[Tuple[str, float]]


@dataclass
class CoverageMetrics:
    """Coverage metrics for detailed analysis."""
    module_name: str
    statements: int
    missing: int
    branches: int
    partial: int
    coverage: float
    missing_lines: List[int]
    uncovered_functions: List[str]


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    test_name: str
    duration: float
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    baseline_duration: Optional[float]
    performance_trend: str  # "improving", "stable", "degrading"


class TestReporter:
    """Comprehensive test reporting with actionable insights."""
    
    def __init__(self, output_dir: str = "test_reports"):
        """Initialize the test reporter."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create subdirectories for different report types
        (self.output_dir / "coverage").mkdir(exist_ok=True)
        (self.output_dir / "performance").mkdir(exist_ok=True)
        (self.output_dir / "junit").mkdir(exist_ok=True)
        (self.output_dir / "trends").mkdir(exist_ok=True)
        
    def run_tests_with_reporting(self, test_mode: str = "sequential", 
                               workers: Optional[int] = None,
                               markers: Optional[str] = None,
                               test_path: Optional[str] = None) -> TestExecutionResult:
        """Run tests and collect comprehensive metrics."""
        print(f"Running tests in {test_mode} mode with comprehensive reporting...")
        
        start_time = time.time()
        
        # Prepare pytest command
        cmd = self._build_pytest_command(test_mode, workers, markers, test_path)
        
        # Run tests and capture output
        result = self._execute_tests(cmd)
        
        execution_time = time.time() - start_time
        
        # Parse test results
        test_result = self._parse_test_results(result, test_mode, workers or 1, execution_time)
        
        # Generate comprehensive reports
        self._generate_all_reports(test_result)
        
        return test_result
    
    def _build_pytest_command(self, test_mode: str, workers: Optional[int], 
                            markers: Optional[str], test_path: Optional[str]) -> List[str]:
        """Build pytest command with comprehensive reporting options."""
        cmd = ["python", "-m", "pytest"]
        
        # Configuration file selection
        if test_mode == "parallel":
            cmd.extend(["-c", "pytest-parallel.ini"])
            if workers:
                cmd.extend(["--numprocesses", str(workers)])
            else:
                cmd.extend(["--numprocesses", "auto"])
            cmd.extend(["--dist", "loadscope"])
        else:
            cmd.extend(["-c", "pytest.ini"])
        
        # Coverage options
        cmd.extend([
            "--cov=src/fqcn_converter",
            "--cov-config=.coveragerc",
            "--cov-report=term-missing",
            f"--cov-report=html:{self.output_dir}/coverage/html_{self.timestamp}",
            f"--cov-report=xml:{self.output_dir}/coverage/coverage_{self.timestamp}.xml",
            f"--cov-report=json:{self.output_dir}/coverage/coverage_{self.timestamp}.json"
        ])
        
        # JUnit XML output
        cmd.extend([
            f"--junit-xml={self.output_dir}/junit/junit_{self.timestamp}.xml",
            "--junit-logging=all",
            "--junit-log-passing-tests=true"
        ])
        
        # Performance and timing options
        cmd.extend([
            "--durations=0",  # Show all test durations
            "--tb=short",
            "--verbose"
        ])
        
        # Test selection
        if markers:
            cmd.extend(["-m", markers])
        
        if test_path:
            cmd.append(test_path)
        
        return cmd
    
    def _execute_tests(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute tests and capture results."""
        print(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            print("Test execution timed out after 30 minutes")
            raise
        except Exception as e:
            print(f"Error executing tests: {e}")
            raise
    
    def _parse_test_results(self, result: subprocess.CompletedProcess, 
                          test_mode: str, workers: int, execution_time: float) -> TestExecutionResult:
        """Parse pytest output to extract test metrics."""
        output = result.stdout + result.stderr
        
        # Parse test counts from pytest output
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        failed_tests = []
        slow_tests = []
        
        # Extract test counts using regex patterns
        import re
        
        # Look for pytest summary line - try multiple patterns
        summary_patterns = [
            r"=+ (\d+) failed,? ?(\d+) passed,? ?(\d+) skipped,? ?(\d+) error",
            r"=+ (\d+) passed,? ?(\d+) skipped",
            r"=+ (\d+) passed",
            r"(\d+) passed, (\d+) skipped",
            r"(\d+) passed"
        ]
        
        parsed = False
        for pattern in summary_patterns:
            match = re.search(pattern, output)
            if match:
                groups = match.groups()
                if len(groups) >= 1:
                    # Handle different summary formats
                    if "failed" in pattern:
                        failed = int(groups[0]) if groups[0] else 0
                        passed = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                        skipped = int(groups[2]) if len(groups) > 2 and groups[2] else 0
                        errors = int(groups[3]) if len(groups) > 3 and groups[3] else 0
                    else:
                        passed = int(groups[0]) if groups[0] else 0
                        skipped = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                parsed = True
                break
        
        if not parsed:
            # Alternative patterns for different pytest output formats
            patterns = [
                (r"(\d+) passed", "passed"),
                (r"(\d+) failed", "failed"), 
                (r"(\d+) skipped", "skipped"),
                (r"(\d+) error", "errors")
            ]
            
            for pattern, test_type in patterns:
                match = re.search(pattern, output)
                if match:
                    count = int(match.group(1))
                    if test_type == "passed":
                        passed = count
                    elif test_type == "failed":
                        failed = count
                    elif test_type == "skipped":
                        skipped = count
                    elif test_type == "errors":
                        errors = count
        
        total_tests = passed + failed + skipped + errors
        
        # Extract failed test names
        failed_pattern = r"FAILED ([\w/._:]+)"
        failed_tests = re.findall(failed_pattern, output)
        
        # Extract slow tests from durations output
        duration_pattern = r"([\d.]+)s call\s+([\w/._:]+)"
        duration_matches = re.findall(duration_pattern, output)
        slow_tests = [(test, float(duration)) for duration, test in duration_matches 
                     if float(duration) > 1.0]  # Tests slower than 1 second
        
        # Get coverage percentage
        coverage_percentage = self._extract_coverage_percentage()
        
        # Debug output
        print(f"Debug: total_tests={total_tests}, passed={passed}, failed={failed}, execution_time={execution_time}")
        
        return TestExecutionResult(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            coverage_percentage=coverage_percentage,
            execution_time=execution_time,
            worker_count=workers,
            test_mode=test_mode,
            timestamp=self.timestamp,
            failed_tests=failed_tests,
            slow_tests=slow_tests
        )
    
    def _extract_coverage_percentage(self) -> float:
        """Extract coverage percentage from coverage reports."""
        coverage_file = self.output_dir / "coverage" / f"coverage_{self.timestamp}.json"
        
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    return coverage_data.get('totals', {}).get('percent_covered', 0.0)
            except Exception as e:
                print(f"Warning: Could not parse coverage data: {e}")
        
        return 0.0
    
    def _generate_all_reports(self, test_result: TestExecutionResult):
        """Generate all comprehensive reports."""
        print("Generating comprehensive test reports...")
        
        # Generate summary report
        self._generate_summary_report(test_result)
        
        # Generate detailed coverage analysis
        self._generate_coverage_analysis()
        
        # Generate performance analysis
        self._generate_performance_analysis(test_result)
        
        # Generate trend analysis
        self._generate_trend_analysis(test_result)
        
        # Generate actionable insights
        self._generate_actionable_insights(test_result)
        
        # Generate CI/CD compatible reports
        self._generate_cicd_reports(test_result)
        
        print(f"All reports generated in: {self.output_dir}")
    
    def _generate_summary_report(self, test_result: TestExecutionResult):
        """Generate executive summary report."""
        summary_file = self.output_dir / f"test_summary_{self.timestamp}.json"
        
        summary = {
            "execution_summary": asdict(test_result),
            "success_rate": (test_result.passed / test_result.total_tests * 100) if test_result.total_tests > 0 else 0,
            "test_efficiency": test_result.total_tests / test_result.execution_time if test_result.execution_time > 0 else 0,
            "recommendations": self._generate_recommendations(test_result)
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Also generate human-readable summary
        self._generate_human_readable_summary(test_result, summary)
    
    def _generate_human_readable_summary(self, test_result: TestExecutionResult, summary: Dict):
        """Generate human-readable summary report."""
        summary_file = self.output_dir / f"test_summary_{self.timestamp}.md"
        
        content = f"""# Test Execution Summary - {test_result.timestamp}

## Overview
- **Test Mode**: {test_result.test_mode}
- **Workers**: {test_result.worker_count}
- **Execution Time**: {test_result.execution_time:.2f} seconds
- **Coverage**: {test_result.coverage_percentage:.2f}%

## Test Results
- **Total Tests**: {test_result.total_tests}
- **Passed**: {test_result.passed} ({test_result.passed/test_result.total_tests*100 if test_result.total_tests > 0 else 0:.1f}%)
- **Failed**: {test_result.failed} ({test_result.failed/test_result.total_tests*100 if test_result.total_tests > 0 else 0:.1f}%)
- **Skipped**: {test_result.skipped} ({test_result.skipped/test_result.total_tests*100 if test_result.total_tests > 0 else 0:.1f}%)
- **Errors**: {test_result.errors} ({test_result.errors/test_result.total_tests*100 if test_result.total_tests > 0 else 0:.1f}%)

## Performance Metrics
- **Success Rate**: {summary['success_rate']:.2f}%
- **Test Efficiency**: {summary['test_efficiency']:.2f} tests/second

## Failed Tests
"""
        
        if test_result.failed_tests:
            for test in test_result.failed_tests:
                content += f"- {test}\n"
        else:
            content += "No failed tests ✅\n"
        
        content += "\n## Slow Tests (>1s)\n"
        if test_result.slow_tests:
            for test, duration in sorted(test_result.slow_tests, key=lambda x: x[1], reverse=True)[:10]:
                content += f"- {test}: {duration:.2f}s\n"
        else:
            content += "No slow tests detected ✅\n"
        
        content += "\n## Recommendations\n"
        for rec in summary['recommendations']:
            content += f"- {rec}\n"
        
        with open(summary_file, 'w') as f:
            f.write(content)
    
    def _generate_coverage_analysis(self):
        """Generate detailed coverage analysis with actionable insights."""
        coverage_json = self.output_dir / "coverage" / f"coverage_{self.timestamp}.json"
        
        if not coverage_json.exists():
            print("Warning: Coverage JSON not found, skipping detailed analysis")
            return
        
        try:
            with open(coverage_json, 'r') as f:
                coverage_data = json.load(f)
            
            analysis = {
                "timestamp": self.timestamp,
                "overall_coverage": coverage_data.get('totals', {}),
                "module_analysis": [],
                "improvement_opportunities": [],
                "critical_gaps": []
            }
            
            # Analyze each module
            for filename, file_data in coverage_data.get('files', {}).items():
                if 'src/fqcn_converter' in filename:
                    module_analysis = self._analyze_module_coverage(filename, file_data)
                    analysis["module_analysis"].append(module_analysis)
                    
                    # Identify improvement opportunities
                    if module_analysis['coverage'] < 90:
                        analysis["improvement_opportunities"].append({
                            "module": filename,
                            "current_coverage": module_analysis['coverage'],
                            "missing_lines": len(module_analysis['missing_lines']),
                            "priority": "high" if module_analysis['coverage'] < 70 else "medium"
                        })
            
            # Save detailed analysis
            analysis_file = self.output_dir / "coverage" / f"coverage_analysis_{self.timestamp}.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            # Generate coverage improvement plan
            self._generate_coverage_improvement_plan(analysis)
            
        except Exception as e:
            print(f"Error generating coverage analysis: {e}")
    
    def _analyze_module_coverage(self, filename: str, file_data: Dict) -> Dict:
        """Analyze coverage for a specific module."""
        summary = file_data.get('summary', {})
        
        return {
            "module": filename,
            "statements": summary.get('num_statements', 0),
            "missing": summary.get('missing_lines', 0),
            "branches": summary.get('num_branches', 0),
            "partial": summary.get('num_partial_branches', 0),
            "coverage": summary.get('percent_covered', 0.0),
            "missing_lines": file_data.get('missing_lines', []),
            "excluded_lines": file_data.get('excluded_lines', [])
        }
    
    def _generate_coverage_improvement_plan(self, analysis: Dict):
        """Generate actionable coverage improvement plan."""
        plan_file = self.output_dir / "coverage" / f"improvement_plan_{self.timestamp}.md"
        
        content = f"""# Coverage Improvement Plan - {analysis['timestamp']}

## Current Status
- **Overall Coverage**: {analysis['overall_coverage'].get('percent_covered', 0):.2f}%
- **Total Statements**: {analysis['overall_coverage'].get('num_statements', 0)}
- **Missing Lines**: {analysis['overall_coverage'].get('missing_lines', 0)}

## Priority Modules for Improvement

"""
        
        # Sort opportunities by priority and coverage
        opportunities = sorted(
            analysis['improvement_opportunities'],
            key=lambda x: (x['priority'] == 'high', -x['current_coverage'])
        )
        
        for opp in opportunities:
            content += f"""### {opp['module']}
- **Current Coverage**: {opp['current_coverage']:.2f}%
- **Missing Lines**: {opp['missing_lines']}
- **Priority**: {opp['priority'].upper()}
- **Recommended Action**: Add {opp['missing_lines']} test cases to cover missing lines

"""
        
        content += """## Implementation Strategy

1. **High Priority Modules**: Focus on modules with <70% coverage first
2. **Test Categories**: Add unit tests for error handling, edge cases, and boundary conditions
3. **Coverage Targets**: Aim for 90%+ coverage on all modules
4. **Monitoring**: Track coverage trends over time

## Next Steps

1. Review missing lines in each module using HTML coverage report
2. Write targeted test cases for uncovered code paths
3. Focus on error handling and edge case scenarios
4. Validate coverage improvements with each test run
"""
        
        with open(plan_file, 'w') as f:
            f.write(content)
    
    def _generate_performance_analysis(self, test_result: TestExecutionResult):
        """Generate performance analysis and trends."""
        perf_file = self.output_dir / "performance" / f"performance_{self.timestamp}.json"
        
        performance_data = {
            "timestamp": self.timestamp,
            "execution_metrics": {
                "total_time": test_result.execution_time,
                "test_count": test_result.total_tests,
                "tests_per_second": test_result.total_tests / test_result.execution_time if test_result.execution_time > 0 else 0,
                "worker_count": test_result.worker_count,
                "test_mode": test_result.test_mode
            },
            "slow_tests": [
                {"test": test, "duration": duration, "threshold_exceeded": duration > 5.0}
                for test, duration in test_result.slow_tests
            ],
            "performance_recommendations": self._generate_performance_recommendations(test_result)
        }
        
        with open(perf_file, 'w') as f:
            json.dump(performance_data, f, indent=2)
        
        # Generate performance report
        self._generate_performance_report(performance_data)
    
    def _generate_performance_report(self, perf_data: Dict):
        """Generate human-readable performance report."""
        report_file = self.output_dir / "performance" / f"performance_report_{self.timestamp}.md"
        
        metrics = perf_data["execution_metrics"]
        
        content = f"""# Performance Analysis Report - {perf_data['timestamp']}

## Execution Metrics
- **Total Execution Time**: {metrics['total_time']:.2f} seconds
- **Test Count**: {metrics['test_count']}
- **Tests per Second**: {metrics['tests_per_second']:.2f}
- **Worker Count**: {metrics['worker_count']}
- **Test Mode**: {metrics['test_mode']}

## Performance Classification
"""
        
        # Classify performance
        if metrics['tests_per_second'] > 10:
            content += "- **Status**: ✅ Excellent performance\n"
        elif metrics['tests_per_second'] > 5:
            content += "- **Status**: ⚠️ Good performance\n"
        elif metrics['tests_per_second'] > 2:
            content += "- **Status**: ⚠️ Acceptable performance\n"
        else:
            content += "- **Status**: ❌ Poor performance - optimization needed\n"
        
        content += "\n## Slow Tests Analysis\n"
        
        slow_tests = perf_data["slow_tests"]
        if slow_tests:
            content += f"Found {len(slow_tests)} slow tests:\n\n"
            for test_data in sorted(slow_tests, key=lambda x: x['duration'], reverse=True)[:10]:
                status = "❌ Critical" if test_data['threshold_exceeded'] else "⚠️ Slow"
                content += f"- {status}: {test_data['test']} ({test_data['duration']:.2f}s)\n"
        else:
            content += "No slow tests detected ✅\n"
        
        content += "\n## Recommendations\n"
        for rec in perf_data["performance_recommendations"]:
            content += f"- {rec}\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
    
    def _generate_performance_recommendations(self, test_result: TestExecutionResult) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        tests_per_second = test_result.total_tests / test_result.execution_time if test_result.execution_time > 0 else 0
        
        if tests_per_second < 2:
            recommendations.append("Consider optimizing test fixtures and setup/teardown operations")
            recommendations.append("Review database operations and consider using in-memory alternatives for tests")
        
        if len(test_result.slow_tests) > 10:
            recommendations.append("Optimize slow tests or consider marking them as integration tests")
            recommendations.append("Use mocking to reduce external dependencies in unit tests")
        
        if test_result.test_mode == "sequential" and test_result.total_tests > 100:
            recommendations.append("Consider running tests in parallel mode to improve execution time")
        
        if test_result.worker_count == 1 and test_result.total_tests > 50:
            recommendations.append("Increase worker count for parallel execution")
        
        return recommendations
    
    def _generate_trend_analysis(self, test_result: TestExecutionResult):
        """Generate trend analysis by comparing with historical data."""
        trends_file = self.output_dir / "trends" / "historical_data.json"
        
        # Load historical data
        historical_data = []
        if trends_file.exists():
            try:
                with open(trends_file, 'r') as f:
                    historical_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load historical data: {e}")
        
        # Add current result
        current_data = asdict(test_result)
        historical_data.append(current_data)
        
        # Keep only last 30 runs
        historical_data = historical_data[-30:]
        
        # Save updated historical data
        trends_file.parent.mkdir(exist_ok=True)
        with open(trends_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        # Generate trend analysis
        if len(historical_data) > 1:
            self._analyze_trends(historical_data)
    
    def _analyze_trends(self, historical_data: List[Dict]):
        """Analyze trends in test execution."""
        trend_analysis = {
            "timestamp": self.timestamp,
            "data_points": len(historical_data),
            "trends": {}
        }
        
        # Analyze coverage trends
        coverage_values = [data['coverage_percentage'] for data in historical_data[-10:]]
        trend_analysis["trends"]["coverage"] = self._calculate_trend(coverage_values)
        
        # Analyze execution time trends
        time_values = [data['execution_time'] for data in historical_data[-10:]]
        trend_analysis["trends"]["execution_time"] = self._calculate_trend(time_values)
        
        # Analyze success rate trends
        success_rates = [
            (data['passed'] / data['total_tests'] * 100) if data['total_tests'] > 0 else 0
            for data in historical_data[-10:]
        ]
        trend_analysis["trends"]["success_rate"] = self._calculate_trend(success_rates)
        
        # Save trend analysis
        trend_file = self.output_dir / "trends" / f"trend_analysis_{self.timestamp}.json"
        with open(trend_file, 'w') as f:
            json.dump(trend_analysis, f, indent=2)
        
        # Generate trend report
        self._generate_trend_report(trend_analysis, historical_data)
    
    def _calculate_trend(self, values: List[float]) -> Dict:
        """Calculate trend direction and statistics."""
        if len(values) < 2:
            return {"direction": "insufficient_data", "change": 0, "stability": "unknown"}
        
        # Simple linear trend calculation
        recent_avg = sum(values[-3:]) / len(values[-3:])
        older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else values[0]
        
        change = recent_avg - older_avg
        change_percent = (change / older_avg * 100) if older_avg != 0 else 0
        
        # Determine trend direction
        if abs(change_percent) < 2:
            direction = "stable"
        elif change_percent > 0:
            direction = "improving" if "coverage" in str(values) or "success" in str(values) else "degrading"
        else:
            direction = "degrading" if "coverage" in str(values) or "success" in str(values) else "improving"
        
        # Calculate stability (coefficient of variation)
        import statistics
        stability = "stable" if len(values) > 1 and statistics.stdev(values) / statistics.mean(values) < 0.1 else "variable"
        
        return {
            "direction": direction,
            "change": change,
            "change_percent": change_percent,
            "stability": stability,
            "recent_average": recent_avg,
            "historical_average": older_avg
        }
    
    def _generate_trend_report(self, trend_analysis: Dict, historical_data: List[Dict]):
        """Generate human-readable trend report."""
        report_file = self.output_dir / "trends" / f"trend_report_{self.timestamp}.md"
        
        content = f"""# Test Execution Trends - {trend_analysis['timestamp']}

## Overview
- **Data Points**: {trend_analysis['data_points']} test runs
- **Analysis Period**: Last {min(10, len(historical_data))} runs

## Trend Analysis

### Coverage Trends
"""
        
        coverage_trend = trend_analysis["trends"]["coverage"]
        content += f"""- **Direction**: {coverage_trend['direction'].replace('_', ' ').title()}
- **Change**: {coverage_trend['change']:.2f}% ({coverage_trend['change_percent']:+.1f}%)
- **Stability**: {coverage_trend['stability'].title()}
- **Current Average**: {coverage_trend['recent_average']:.2f}%

"""
        
        exec_trend = trend_analysis["trends"]["execution_time"]
        content += f"""### Execution Time Trends
- **Direction**: {exec_trend['direction'].replace('_', ' ').title()}
- **Change**: {exec_trend['change']:+.2f}s ({exec_trend['change_percent']:+.1f}%)
- **Stability**: {exec_trend['stability'].title()}
- **Current Average**: {exec_trend['recent_average']:.2f}s

"""
        
        success_trend = trend_analysis["trends"]["success_rate"]
        content += f"""### Success Rate Trends
- **Direction**: {success_trend['direction'].replace('_', ' ').title()}
- **Change**: {success_trend['change']:+.2f}% ({success_trend['change_percent']:+.1f}%)
- **Stability**: {success_trend['stability'].title()}
- **Current Average**: {success_trend['recent_average']:.2f}%

## Recommendations

"""
        
        # Generate trend-based recommendations
        recommendations = []
        
        if coverage_trend['direction'] == 'degrading':
            recommendations.append("Coverage is declining - review recent changes and add missing tests")
        elif coverage_trend['direction'] == 'stable' and coverage_trend['recent_average'] < 90:
            recommendations.append("Coverage is stable but below target - focus on improving low-coverage modules")
        
        if exec_trend['direction'] == 'degrading':
            recommendations.append("Execution time is increasing - profile slow tests and optimize performance")
        
        if success_trend['direction'] == 'degrading':
            recommendations.append("Success rate is declining - investigate and fix failing tests immediately")
        
        if not recommendations:
            recommendations.append("All trends are positive - maintain current testing practices")
        
        for rec in recommendations:
            content += f"- {rec}\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
    
    def _generate_actionable_insights(self, test_result: TestExecutionResult):
        """Generate actionable insights based on test results."""
        insights_file = self.output_dir / f"actionable_insights_{self.timestamp}.md"
        
        content = f"""# Actionable Test Insights - {test_result.timestamp}

## Immediate Actions Required

"""
        
        # Critical issues
        if test_result.failed > 0:
            content += f"""### 🚨 Critical: {test_result.failed} Failed Tests
**Priority**: Immediate
**Action**: Fix failing tests before proceeding with development

Failed tests:
"""
            for test in test_result.failed_tests:
                content += f"- {test}\n"
            content += "\n"
        
        if test_result.coverage_percentage < 80:
            content += f"""### ⚠️ Low Coverage: {test_result.coverage_percentage:.1f}%
**Priority**: High
**Action**: Increase test coverage to at least 90%
**Target**: Add approximately {int((90 - test_result.coverage_percentage) * 10)} test cases

"""
        
        # Performance issues
        critical_slow_tests = [t for t, d in test_result.slow_tests if d > 10]
        if critical_slow_tests:
            content += f"""### 🐌 Performance Issues: {len(critical_slow_tests)} Very Slow Tests
**Priority**: Medium
**Action**: Optimize tests taking >10 seconds

Critical slow tests:
"""
            for test in critical_slow_tests:
                content += f"- {test}\n"
            content += "\n"
        
        content += """## Improvement Opportunities

### Test Coverage Enhancement
1. Review HTML coverage report for specific missing lines
2. Focus on error handling and edge case scenarios
3. Add integration tests for end-to-end workflows
4. Implement property-based testing for complex logic

### Performance Optimization
1. Profile slow tests to identify bottlenecks
2. Use mocking to reduce external dependencies
3. Optimize test fixtures and setup/teardown
4. Consider parallel execution for large test suites

### Test Quality Improvements
1. Add more descriptive test names and documentation
2. Implement test categorization with markers
3. Add regression tests for bug fixes
4. Enhance error messages and assertions

## Monitoring and Maintenance

### Regular Tasks
- [ ] Review test results weekly
- [ ] Monitor coverage trends monthly
- [ ] Update performance baselines quarterly
- [ ] Refactor slow tests as needed

### Automation Opportunities
- [ ] Set up automated coverage reporting in CI/CD
- [ ] Implement performance regression detection
- [ ] Add automatic test result notifications
- [ ] Create coverage improvement tracking

## Success Metrics

### Short-term (1-2 weeks)
- [ ] Zero failing tests
- [ ] >90% code coverage
- [ ] <5 second average test execution time

### Medium-term (1 month)
- [ ] >95% code coverage
- [ ] Stable performance trends
- [ ] Comprehensive integration test suite

### Long-term (3 months)
- [ ] 100% automated test coverage reporting
- [ ] Performance benchmarking and regression detection
- [ ] Comprehensive test documentation and maintenance procedures
"""
        
        with open(insights_file, 'w') as f:
            f.write(content)
    
    def _generate_cicd_reports(self, test_result: TestExecutionResult):
        """Generate CI/CD compatible reports."""
        # Generate GitHub Actions summary
        if os.getenv('GITHUB_ACTIONS'):
            self._generate_github_summary(test_result)
        
        # Generate generic CI/CD summary
        self._generate_generic_cicd_summary(test_result)
    
    def _generate_github_summary(self, test_result: TestExecutionResult):
        """Generate GitHub Actions job summary."""
        summary_file = self.output_dir / f"github_summary_{self.timestamp}.md"
        
        # Determine status emoji
        if test_result.failed == 0 and test_result.errors == 0:
            status_emoji = "✅"
            status_text = "All tests passed"
        else:
            status_emoji = "❌"
            status_text = f"{test_result.failed + test_result.errors} tests failed"
        
        content = f"""# {status_emoji} Test Results Summary

## {status_text}

| Metric | Value |
|--------|-------|
| Total Tests | {test_result.total_tests} |
| Passed | {test_result.passed} |
| Failed | {test_result.failed} |
| Skipped | {test_result.skipped} |
| Errors | {test_result.errors} |
| Coverage | {test_result.coverage_percentage:.2f}% |
| Execution Time | {test_result.execution_time:.2f}s |
| Test Mode | {test_result.test_mode} |

## Coverage Status
"""
        
        if test_result.coverage_percentage >= 95:
            content += "🟢 Excellent coverage (≥95%)\n"
        elif test_result.coverage_percentage >= 90:
            content += "🟡 Good coverage (≥90%)\n"
        elif test_result.coverage_percentage >= 80:
            content += "🟠 Acceptable coverage (≥80%)\n"
        else:
            content += "🔴 Low coverage (<80%) - Improvement needed\n"
        
        if test_result.failed_tests:
            content += "\n## Failed Tests\n"
            for test in test_result.failed_tests[:10]:  # Limit to first 10
                content += f"- {test}\n"
            if len(test_result.failed_tests) > 10:
                content += f"... and {len(test_result.failed_tests) - 10} more\n"
        
        with open(summary_file, 'w') as f:
            f.write(content)
    
    def _generate_generic_cicd_summary(self, test_result: TestExecutionResult):
        """Generate generic CI/CD compatible summary."""
        summary = {
            "test_results": {
                "total": test_result.total_tests,
                "passed": test_result.passed,
                "failed": test_result.failed,
                "skipped": test_result.skipped,
                "errors": test_result.errors,
                "success_rate": (test_result.passed / test_result.total_tests * 100) if test_result.total_tests > 0 else 0
            },
            "coverage": {
                "percentage": test_result.coverage_percentage,
                "status": "pass" if test_result.coverage_percentage >= 90 else "fail"
            },
            "performance": {
                "execution_time": test_result.execution_time,
                "tests_per_second": test_result.total_tests / test_result.execution_time if test_result.execution_time > 0 else 0
            },
            "status": "success" if test_result.failed == 0 and test_result.errors == 0 else "failure",
            "timestamp": test_result.timestamp
        }
        
        summary_file = self.output_dir / f"cicd_summary_{self.timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def _generate_recommendations(self, test_result: TestExecutionResult) -> List[str]:
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        if test_result.failed > 0:
            recommendations.append(f"Fix {test_result.failed} failing tests immediately")
        
        if test_result.coverage_percentage < 90:
            recommendations.append(f"Improve coverage from {test_result.coverage_percentage:.1f}% to 90%+")
        
        if len(test_result.slow_tests) > 5:
            recommendations.append("Optimize slow tests to improve execution time")
        
        if test_result.test_mode == "sequential" and test_result.total_tests > 100:
            recommendations.append("Consider parallel test execution to reduce runtime")
        
        if test_result.execution_time > 300:  # 5 minutes
            recommendations.append("Test suite is taking too long - consider optimization")
        
        return recommendations


def main():
    """Main entry point for test reporting."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Reporting System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--mode", choices=["sequential", "parallel"], 
                       default="sequential", help="Test execution mode")
    parser.add_argument("--workers", type=int, help="Number of workers for parallel mode")
    parser.add_argument("--markers", help="Test markers to select")
    parser.add_argument("--test-path", help="Specific test path to run")
    parser.add_argument("--output-dir", default="test_reports", 
                       help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Initialize reporter
    reporter = TestReporter(args.output_dir)
    
    try:
        # Run tests with comprehensive reporting
        result = reporter.run_tests_with_reporting(
            test_mode=args.mode,
            workers=args.workers,
            markers=args.markers,
            test_path=args.test_path
        )
        
        print(f"\n{'='*60}")
        print("TEST EXECUTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Tests: {result.total_tests}")
        print(f"Passed: {result.passed}")
        print(f"Failed: {result.failed}")
        print(f"Coverage: {result.coverage_percentage:.2f}%")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Reports generated in: {reporter.output_dir}")
        
        # Exit with appropriate code
        sys.exit(0 if result.failed == 0 and result.errors == 0 else 1)
        
    except Exception as e:
        print(f"Error during test execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()