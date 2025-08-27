# Performance Monitoring and Baselines

This document describes the comprehensive performance monitoring and baseline system implemented for the FQCN Converter project.

## Overview

The performance monitoring system provides:

- **Baseline Establishment**: Automatic establishment of performance baselines for different system configurations
- **Adaptive Thresholds**: Performance thresholds that adapt to hardware capabilities
- **Statistical Analysis**: Comprehensive statistical analysis including trend detection and anomaly identification
- **Performance Tracking**: Continuous tracking of performance metrics with trend analysis
- **Comprehensive Reporting**: Detailed reports with actionable insights and recommendations

## Components

### 1. Performance Baselines (`performance_baselines.py`)

Manages performance baselines for different operations and system configurations.

**Key Features:**
- Establishes baselines through multiple measurement runs
- Stores baselines with confidence intervals and statistical measures
- Provides adaptive performance thresholds based on system capabilities
- Validates current performance against established baselines

**Usage:**
```python
from tests.fixtures.performance_baselines import PerformanceBaselineManager

manager = PerformanceBaselineManager()

# Establish baseline for an operation
baseline = manager.establish_baseline(
    "file_conversion", 
    conversion_function, 
    parameter_sets, 
    min_samples=5
)

# Validate performance
is_valid, message = manager.validate_performance("file_conversion", actual_duration)
```

### 2. Performance Monitor (`performance_monitor.py`)

Provides decorators and context managers for easy performance monitoring integration.

**Usage:**
```python
from tests.fixtures.performance_monitor import monitor_performance, measure_operation

# Decorator usage
@monitor_performance("operation_name")
def my_function():
    # Function implementation
    pass

# Context manager usage
with measure_operation("operation_name", parameters={"param": "value"}):
    # Code to monitor
    pass
```

### 3. Performance Statistics (`performance_statistics.py`)

Provides statistical analysis capabilities for performance data.

**Features:**
- Statistical summaries (mean, median, percentiles, etc.)
- Anomaly detection using multiple methods (IQR, Z-score, Modified Z-score)
- Trend analysis with linear regression
- Distribution comparison between baseline and current measurements

### 4. Performance Reporter (`performance_reporter.py`)

Generates comprehensive performance reports in multiple formats.

**Features:**
- JSON and HTML report generation
- Trend analysis and recommendations
- Anomaly detection summaries
- Performance insights and actionable recommendations

## System Capabilities Detection

The system automatically detects hardware capabilities and adjusts performance expectations:

- **CPU Performance**: Measures relative CPU speed through benchmark operations
- **I/O Performance**: Measures relative I/O speed through file operations
- **Memory**: Detects available system memory
- **Core Count**: Detects number of CPU cores for parallel processing expectations

## Adaptive Performance Thresholds

Performance thresholds automatically adapt based on:

1. **System Capabilities**: Slower systems get more lenient thresholds
2. **Operation Type**: Different operations (CPU-bound, I/O-bound, mixed) have different scaling factors
3. **Data Size**: Larger datasets may have different performance characteristics
4. **Historical Performance**: Baselines are established from actual system performance

## Performance Test Integration

### Pytest Plugin

The system includes a pytest plugin that automatically monitors performance tests:

```python
@pytest.mark.performance
def test_my_performance():
    # Test implementation
    pass
```

The plugin automatically:
- Records performance measurements
- Validates against baselines
- Generates session summaries
- Integrates with the baseline system

### Test Fixtures

Enhanced test fixtures support performance monitoring:

- `isolated_temp_dir`: Worker-specific temporary directories for parallel execution
- `mock_config_manager`: Thread-safe configuration mocking
- `test_environment_setup`: Consistent test environment configuration

## Usage Examples

### Establishing Baselines

```bash
# Establish baselines for common operations
python scripts/performance_baseline_setup.py --establish-baselines

# Generate performance reports
python scripts/performance_baseline_setup.py --generate-report
```

### Running Performance Tests

```bash
# Run performance tests with baseline establishment
python scripts/run_performance_tests.py --establish-baselines

# Run performance tests and generate reports
python scripts/run_performance_tests.py --generate-report

# Run specific performance test pattern
python scripts/run_performance_tests.py --test-pattern test_large_file
```

### Manual Performance Monitoring

```python
from tests.fixtures.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# Monitor a function
@monitor.monitor_performance("my_operation")
def my_function():
    # Implementation
    pass

# Generate reports
report = monitor.get_performance_report()
```

## Report Structure

### Comprehensive Report

```json
{
  "generated_at": "2025-08-27T15:51:13.032976+00:00",
  "system_config": {
    "cpu_cores": 8,
    "memory_gb": 16.0,
    "cpu_speed_factor": 10.0,
    "io_speed_factor": 1.31
  },
  "baselines": {
    "operation_name": {
      "baseline_time": 0.052,
      "std_deviation": 0.002,
      "confidence_interval": [0.049, 0.055],
      "sample_count": 5
    }
  },
  "detailed_analysis": {
    "operation_name": {
      "statistical_summary": { /* ... */ },
      "trend_analysis": {
        "direction": "stable",
        "slope": 0.001,
        "correlation": 0.95,
        "significance": 0.8
      },
      "anomaly_count": 0,
      "stability_assessment": {
        "is_stable": true,
        "coefficient_of_variation": 0.03,
        "stability_rating": "excellent"
      }
    }
  },
  "recommendations": [
    {
      "operation": "operation_name",
      "priority": "medium",
      "type": "performance_instability",
      "description": "Performance recommendation",
      "suggested_actions": ["action1", "action2"]
    }
  ]
}
```

### Trend Report

```json
{
  "generated_at": "2025-08-27T15:51:13.032976+00:00",
  "period_days": 30,
  "trends": {
    "operation_name": {
      "measurement_count": 10,
      "mean_duration": 0.052,
      "trend_direction": "improving",
      "trend_slope": -0.001,
      "recent_measurements": [0.051, 0.050, 0.049]
    }
  }
}
```

## Configuration

### Baseline Storage

Baselines are stored in `test_reports/performance/baselines.json` by default. The location can be configured:

```python
manager = PerformanceBaselineManager(baseline_file=Path("custom/baselines.json"))
```

### Performance Thresholds

Default tolerance factors can be adjusted:

```python
# More strict validation (1.5x tolerance instead of 2.0x)
with measure_operation("operation", tolerance_factor=1.5):
    # Code to monitor
    pass
```

### Report Output

Report output directory can be configured:

```python
reporter = PerformanceReporter()
reporter.report_dir = Path("custom/reports")
```

## Best Practices

1. **Establish Baselines Early**: Run baseline establishment on representative hardware before running performance tests
2. **Use Appropriate Tolerance**: Set tolerance factors based on operation criticality and expected variability
3. **Monitor Trends**: Regularly review trend reports to identify performance degradation early
4. **System-Specific Baselines**: Establish separate baselines for different deployment environments
5. **Regular Baseline Updates**: Re-establish baselines when significant code changes are made

## Troubleshooting

### Common Issues

1. **Circular Import Errors**: Ensure imports are done within functions when necessary to avoid circular dependencies
2. **Insufficient Measurements**: Ensure at least 3 measurements for statistical analysis
3. **JSON Serialization**: Use `.to_dict()` methods for complex objects in reports
4. **File Permissions**: Ensure write permissions for baseline and report directories

### Performance Debugging

1. Check system capabilities: `PerformanceUtils.get_system_capabilities()`
2. Review baseline establishment logs for errors
3. Examine detailed analysis in comprehensive reports
4. Use trend reports to identify performance patterns

## Integration with CI/CD

The performance monitoring system integrates with CI/CD pipelines:

1. **Baseline Establishment**: Run during environment setup
2. **Performance Testing**: Include in test suites with appropriate thresholds
3. **Report Generation**: Generate reports as build artifacts
4. **Trend Monitoring**: Track performance trends across builds

Example CI integration:

```yaml
- name: Establish Performance Baselines
  run: python scripts/performance_baseline_setup.py --establish-baselines

- name: Run Performance Tests
  run: python scripts/run_performance_tests.py --generate-report

- name: Archive Performance Reports
  uses: actions/upload-artifact@v2
  with:
    name: performance-reports
    path: test_reports/performance/
```

This comprehensive performance monitoring system ensures that performance regressions are caught early and provides actionable insights for performance optimization.