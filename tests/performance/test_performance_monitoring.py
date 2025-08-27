"""
Tests for the performance monitoring and baseline system.

This module tests the performance monitoring infrastructure including
baselines, statistical analysis, and reporting functionality.
"""

import time
import tempfile
from pathlib import Path

import pytest

from tests.fixtures.performance_baselines import PerformanceBaselineManager, PerformanceMeasurement
from tests.fixtures.performance_monitor import PerformanceMonitor, monitor_performance, measure_operation
from tests.fixtures.performance_statistics import PerformanceStatistics, TrendDirection
from tests.fixtures.performance_reporter import PerformanceReporter


@pytest.mark.performance
class TestPerformanceBaselines:
    """Test performance baseline functionality."""
    
    def test_baseline_establishment(self, isolated_temp_dir):
        """Test establishing performance baselines."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        
        # Define a simple test function
        def test_operation(duration=0.1):
            time.sleep(duration)
            return "completed"
        
        # Establish baseline with different parameters
        parameter_sets = [
            {"duration": 0.05},
            {"duration": 0.1},
            {"duration": 0.15}
        ]
        
        baseline = manager.establish_baseline(
            "test_operation", test_operation, parameter_sets, min_samples=3
        )
        
        assert baseline.operation_name == "test_operation"
        assert baseline.baseline_time > 0
        assert baseline.sample_count >= 9  # 3 parameter sets * 3 samples
        assert baseline.confidence_interval[0] <= baseline.baseline_time <= baseline.confidence_interval[1]
        
        # Verify baseline is saved and can be retrieved
        retrieved_baseline = manager.get_baseline("test_operation")
        assert retrieved_baseline is not None
        assert retrieved_baseline.operation_name == baseline.operation_name
    
    def test_performance_validation(self, isolated_temp_dir):
        """Test performance validation against baselines."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        
        # Establish a baseline first
        def fast_operation():
            time.sleep(0.01)
        
        manager.establish_baseline(
            "fast_operation", fast_operation, [{}], min_samples=3
        )
        
        # Test validation with good performance
        is_valid, message = manager.validate_performance("fast_operation", 0.02)
        assert is_valid, f"Good performance should be valid: {message}"
        
        # Test validation with poor performance
        is_valid, message = manager.validate_performance("fast_operation", 1.0)
        assert not is_valid, f"Poor performance should be invalid: {message}"
    
    def test_measurement_recording(self, isolated_temp_dir):
        """Test recording performance measurements."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        
        # Record some measurements
        manager.record_measurement("test_op", 0.1, {"param": 1}, success=True)
        manager.record_measurement("test_op", 0.15, {"param": 2}, success=True)
        manager.record_measurement("test_op", 0.2, {"param": 3}, success=False)
        
        assert len(manager._measurements) == 3
        
        # Check measurements are saved and loaded
        manager._save_measurements()
        new_manager = PerformanceBaselineManager(baseline_file)
        assert len(new_manager._measurements) == 3


@pytest.mark.performance
class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def test_monitor_decorator(self, isolated_temp_dir):
        """Test performance monitoring decorator."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        monitor = PerformanceMonitor(manager)
        
        @monitor.monitor_performance("decorated_operation", validate_against_baseline=False)
        def test_function(duration=0.05):
            time.sleep(duration)
            return "success"
        
        result = test_function(duration=0.1)
        assert result == "success"
        
        # Check that measurement was recorded
        assert len(manager._measurements) > 0
        measurement = manager._measurements[-1]
        assert measurement.operation_name == "decorated_operation"
        assert measurement.duration >= 0.1
        assert measurement.success
    
    def test_context_manager(self, isolated_temp_dir):
        """Test performance monitoring context manager."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        monitor = PerformanceMonitor(manager)
        
        with monitor.measure_operation("context_operation", 
                                     parameters={"test_param": 42},
                                     validate_against_baseline=False):
            time.sleep(0.05)
        
        # Check that measurement was recorded
        assert len(manager._measurements) > 0
        measurement = manager._measurements[-1]
        assert measurement.operation_name == "context_operation"
        assert measurement.parameters["test_param"] == 42
        assert measurement.success
    
    def test_global_monitor_functions(self):
        """Test global monitor convenience functions."""
        @monitor_performance("global_test_operation", validate_against_baseline=False)
        def test_function():
            time.sleep(0.02)
            return "done"
        
        result = test_function()
        assert result == "done"
        
        # Test context manager
        with measure_operation("global_context_operation", validate_against_baseline=False):
            time.sleep(0.02)


@pytest.mark.performance
class TestPerformanceStatistics:
    """Test performance statistics functionality."""
    
    def test_statistical_summary(self):
        """Test statistical summary calculation."""
        measurements = [0.1, 0.12, 0.11, 0.13, 0.09, 0.14, 0.10, 0.11, 0.12, 0.10]
        
        summary = PerformanceStatistics.calculate_summary(measurements)
        
        assert summary.count == 10
        assert 0.10 <= summary.mean <= 0.13
        assert summary.min_value == 0.09
        assert summary.max_value == 0.14
        assert summary.median == 0.11
        assert summary.std_deviation > 0
    
    def test_anomaly_detection(self):
        """Test anomaly detection methods."""
        # Normal measurements with one outlier
        measurements = [0.1, 0.11, 0.12, 0.10, 0.11, 0.5, 0.12, 0.10]  # 0.5 is an outlier
        
        # Test IQR method
        iqr_anomalies = PerformanceStatistics.detect_anomalies(measurements, method="iqr")
        assert len(iqr_anomalies) > 0
        assert any(anomaly.is_anomaly for anomaly in iqr_anomalies)
        
        # Test Z-score method
        zscore_anomalies = PerformanceStatistics.detect_anomalies(measurements, method="zscore")
        assert len(zscore_anomalies) > 0
        
        # Test Modified Z-score method
        modified_anomalies = PerformanceStatistics.detect_anomalies(measurements, method="modified_zscore")
        assert len(modified_anomalies) > 0
    
    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        # Improving trend (decreasing times)
        improving_measurements = [0.2, 0.18, 0.16, 0.14, 0.12, 0.10]
        improving_trend = PerformanceStatistics.analyze_trend(improving_measurements)
        assert improving_trend.direction == TrendDirection.IMPROVING
        assert improving_trend.slope < 0
        
        # Degrading trend (increasing times)
        degrading_measurements = [0.1, 0.12, 0.14, 0.16, 0.18, 0.20]
        degrading_trend = PerformanceStatistics.analyze_trend(degrading_measurements)
        assert degrading_trend.direction == TrendDirection.DEGRADING
        assert degrading_trend.slope > 0
        
        # Stable trend
        stable_measurements = [0.1, 0.1, 0.1, 0.1, 0.1]
        stable_trend = PerformanceStatistics.analyze_trend(stable_measurements)
        assert stable_trend.direction == TrendDirection.STABLE
    
    def test_distribution_comparison(self):
        """Test distribution comparison functionality."""
        baseline_measurements = [0.1, 0.11, 0.12, 0.10, 0.11]
        current_measurements = [0.15, 0.16, 0.17, 0.14, 0.16]  # Slower performance
        
        comparison = PerformanceStatistics.compare_distributions(
            baseline_measurements, current_measurements
        )
        
        assert "baseline_summary" in comparison
        assert "current_summary" in comparison
        assert comparison["mean_difference"] > 0  # Current is slower
        assert comparison["percent_change"] > 0
        assert comparison["performance_change"] == "degraded"


@pytest.mark.performance
class TestPerformanceReporter:
    """Test performance reporting functionality."""
    
    def test_comprehensive_report_generation(self, isolated_temp_dir):
        """Test comprehensive performance report generation."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        
        # Add some test data
        manager.record_measurement("test_operation", 0.1, {"param": 1}, success=True)
        manager.record_measurement("test_operation", 0.12, {"param": 2}, success=True)
        manager.record_measurement("test_operation", 0.11, {"param": 3}, success=True)
        
        reporter = PerformanceReporter(manager)
        reporter.report_dir = isolated_temp_dir
        
        report = reporter.generate_comprehensive_report()
        
        assert "generated_at" in report
        assert "system_config" in report
        assert "summary" in report
        assert "detailed_analysis" in report
        assert "recommendations" in report
        assert "anomaly_detection" in report
        
        # Check that files were created
        json_files = list(isolated_temp_dir.glob("performance_report_*.json"))
        html_files = list(isolated_temp_dir.glob("performance_report_*.html"))
        
        assert len(json_files) > 0
        assert len(html_files) > 0
    
    def test_trend_report_generation(self, isolated_temp_dir):
        """Test trend report generation."""
        baseline_file = isolated_temp_dir / "test_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        
        # Add measurements over time
        for i in range(10):
            manager.record_measurement("trending_operation", 0.1 + i * 0.01, {"iteration": i}, success=True)
        
        reporter = PerformanceReporter(manager)
        trend_report = reporter.generate_trend_report(days_back=1)
        
        assert "generated_at" in trend_report
        assert "trends" in trend_report
        assert "trending_operation" in trend_report["trends"]


@pytest.mark.performance
class TestPerformanceIntegration:
    """Integration tests for the complete performance monitoring system."""
    
    def test_end_to_end_monitoring(self, isolated_temp_dir):
        """Test complete end-to-end performance monitoring workflow."""
        # Set up monitoring
        baseline_file = isolated_temp_dir / "integration_baselines.json"
        manager = PerformanceBaselineManager(baseline_file)
        monitor = PerformanceMonitor(manager)
        
        # Define test operations
        @monitor.monitor_performance("integration_test", validate_against_baseline=False)
        def slow_operation(duration=0.1):
            time.sleep(duration)
            return "completed"
        
        def fast_operation(duration=0.05):
            time.sleep(duration)
            return "completed"
        
        # Establish baseline for fast operation
        monitor.establish_baseline_for_function(
            fast_operation, "fast_baseline_test", [{"duration": 0.05}], min_samples=3
        )
        
        # Run monitored operations (need at least 3 for analysis)
        slow_operation(duration=0.08)
        slow_operation(duration=0.12)
        slow_operation(duration=0.10)
        
        # Test validation
        with monitor.measure_operation("fast_baseline_test", 
                                     parameters={"duration": 0.05},
                                     validate_against_baseline=True):
            fast_operation(duration=0.05)
        
        # Generate reports
        reporter = PerformanceReporter(manager)
        reporter.report_dir = isolated_temp_dir
        
        comprehensive_report = reporter.generate_comprehensive_report()
        trend_report = reporter.generate_trend_report()
        
        # Verify data was collected
        assert len(manager._measurements) >= 7  # 3 baseline + 3 slow + 1 fast
        assert len(manager._baselines) >= 1
        
        # Verify reports contain expected data
        assert comprehensive_report["summary"]["total_measurements"] >= 7
        # Check for either operation in detailed analysis (need at least 3 measurements)
        detailed_analysis = comprehensive_report.get("detailed_analysis", {})
        assert len(detailed_analysis) > 0, "Should have detailed analysis for operations with enough measurements"
        
        print(f"Integration test completed successfully:")
        print(f"  - Measurements recorded: {len(manager._measurements)}")
        print(f"  - Baselines established: {len(manager._baselines)}")
        print(f"  - Reports generated: comprehensive + trend")