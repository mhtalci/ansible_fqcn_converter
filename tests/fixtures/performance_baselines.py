"""
Performance baseline management for adaptive performance testing.

This module provides functionality to establish, store, and retrieve
performance baselines for different system configurations and operations.
"""

import json
import time
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .performance_utils import PerformanceUtils, SystemCapabilities


@dataclass
class PerformanceBaseline:
    """Performance baseline for a specific operation and system configuration."""
    operation_name: str
    system_config: Dict[str, Any]
    baseline_time: float
    std_deviation: float
    sample_count: int
    confidence_interval: Tuple[float, float]
    created_at: str
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceBaseline':
        """Create from dictionary loaded from JSON."""
        return cls(**data)


@dataclass
class PerformanceMeasurement:
    """Single performance measurement."""
    operation_name: str
    duration: float
    system_config: Dict[str, Any]
    parameters: Dict[str, Any]
    timestamp: str
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PerformanceBaselineManager:
    """Manages performance baselines and measurements."""
    
    def __init__(self, baseline_file: Optional[Path] = None):
        """Initialize baseline manager."""
        self.baseline_file = baseline_file or Path("test_reports/performance/baselines.json")
        self.measurements_file = self.baseline_file.parent / "measurements.json"
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._baselines: Dict[str, PerformanceBaseline] = {}
        self._measurements: List[PerformanceMeasurement] = []
        self._load_baselines()
        self._load_measurements()
    
    def _load_baselines(self) -> None:
        """Load existing baselines from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    data = json.load(f)
                    self._baselines = {
                        key: PerformanceBaseline.from_dict(baseline_data)
                        for key, baseline_data in data.items()
                    }
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load baselines from {self.baseline_file}: {e}")
                self._baselines = {}
    
    def _load_measurements(self) -> None:
        """Load existing measurements from file."""
        if self.measurements_file.exists():
            try:
                with open(self.measurements_file, 'r') as f:
                    data = json.load(f)
                    self._measurements = [
                        PerformanceMeasurement(**measurement_data)
                        for measurement_data in data
                    ]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load measurements from {self.measurements_file}: {e}")
                self._measurements = []
    
    def _save_baselines(self) -> None:
        """Save baselines to file."""
        data = {key: baseline.to_dict() for key, baseline in self._baselines.items()}
        with open(self.baseline_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_measurements(self) -> None:
        """Save measurements to file."""
        # Keep only the last 1000 measurements to prevent file from growing too large
        recent_measurements = self._measurements[-1000:]
        data = [measurement.to_dict() for measurement in recent_measurements]
        with open(self.measurements_file, 'w') as f:
            json.dump(data, f, indent=2)
        self._measurements = recent_measurements
    
    def _get_baseline_key(self, operation_name: str, system_config: Dict[str, Any]) -> str:
        """Generate a unique key for baseline storage."""
        # Create a simplified system config key
        key_parts = [
            operation_name,
            f"cores_{system_config.get('cpu_cores', 'unknown')}",
            f"mem_{system_config.get('memory_gb', 'unknown'):.1f}GB",
            f"cpu_{system_config.get('cpu_speed_factor', 'unknown'):.2f}",
            f"io_{system_config.get('io_speed_factor', 'unknown'):.2f}"
        ]
        return "_".join(str(part) for part in key_parts)
    
    def record_measurement(self, operation_name: str, duration: float, 
                          parameters: Optional[Dict[str, Any]] = None,
                          success: bool = True) -> None:
        """Record a performance measurement."""
        system_capabilities = PerformanceUtils.get_system_capabilities()
        system_config = asdict(system_capabilities)
        
        measurement = PerformanceMeasurement(
            operation_name=operation_name,
            duration=duration,
            system_config=system_config,
            parameters=parameters or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=success
        )
        
        self._measurements.append(measurement)
        self._save_measurements()
    
    def establish_baseline(self, operation_name: str, 
                          measurement_func: callable,
                          parameters_list: List[Dict[str, Any]],
                          min_samples: int = 5) -> PerformanceBaseline:
        """Establish a performance baseline by running multiple measurements."""
        system_capabilities = PerformanceUtils.get_system_capabilities()
        system_config = asdict(system_capabilities)
        
        durations = []
        successful_runs = 0
        
        print(f"Establishing baseline for {operation_name} with {len(parameters_list)} parameter sets...")
        
        for params in parameters_list:
            for run in range(min_samples):
                try:
                    start_time = time.time()
                    measurement_func(**params)
                    duration = time.time() - start_time
                    durations.append(duration)
                    successful_runs += 1
                    
                    # Record individual measurement
                    self.record_measurement(operation_name, duration, params, success=True)
                    
                except Exception as e:
                    print(f"Warning: Baseline measurement failed for {operation_name}: {e}")
                    self.record_measurement(operation_name, 0.0, params, success=False)
        
        if len(durations) < min_samples:
            raise ValueError(f"Insufficient successful measurements for baseline: {len(durations)} < {min_samples}")
        
        # Calculate statistical measures
        baseline_time = statistics.mean(durations)
        std_deviation = statistics.stdev(durations) if len(durations) > 1 else 0.0
        
        # Calculate 95% confidence interval
        if len(durations) > 1:
            # Using t-distribution approximation for small samples
            import math
            t_value = 2.0  # Approximate t-value for 95% confidence with small samples
            margin_of_error = t_value * (std_deviation / math.sqrt(len(durations)))
            confidence_interval = (
                baseline_time - margin_of_error,
                baseline_time + margin_of_error
            )
        else:
            confidence_interval = (baseline_time, baseline_time)
        
        # Create baseline
        now = datetime.now(timezone.utc).isoformat()
        baseline = PerformanceBaseline(
            operation_name=operation_name,
            system_config=system_config,
            baseline_time=baseline_time,
            std_deviation=std_deviation,
            sample_count=len(durations),
            confidence_interval=confidence_interval,
            created_at=now,
            last_updated=now
        )
        
        # Store baseline
        baseline_key = self._get_baseline_key(operation_name, system_config)
        self._baselines[baseline_key] = baseline
        self._save_baselines()
        
        print(f"Baseline established for {operation_name}: {baseline_time:.3f}s ± {std_deviation:.3f}s")
        return baseline
    
    def get_baseline(self, operation_name: str) -> Optional[PerformanceBaseline]:
        """Get baseline for current system configuration."""
        system_capabilities = PerformanceUtils.get_system_capabilities()
        system_config = asdict(system_capabilities)
        baseline_key = self._get_baseline_key(operation_name, system_config)
        
        return self._baselines.get(baseline_key)
    
    def get_adaptive_threshold(self, operation_name: str, 
                             tolerance_factor: float = 2.0) -> Optional[float]:
        """Get adaptive performance threshold based on baseline."""
        baseline = self.get_baseline(operation_name)
        if not baseline:
            return None
        
        # Use confidence interval upper bound plus tolerance
        upper_confidence = baseline.confidence_interval[1]
        adaptive_threshold = upper_confidence * tolerance_factor
        
        return adaptive_threshold
    
    def validate_performance(self, operation_name: str, actual_duration: float,
                           tolerance_factor: float = 2.0) -> Tuple[bool, str]:
        """Validate performance against baseline."""
        baseline = self.get_baseline(operation_name)
        if not baseline:
            return True, f"No baseline available for {operation_name}"
        
        threshold = self.get_adaptive_threshold(operation_name, tolerance_factor)
        
        if actual_duration <= threshold:
            return True, f"Performance within expectations: {actual_duration:.3f}s <= {threshold:.3f}s"
        else:
            return False, (
                f"Performance below expectations: {actual_duration:.3f}s > {threshold:.3f}s "
                f"(baseline: {baseline.baseline_time:.3f}s ± {baseline.std_deviation:.3f}s)"
            )
    
    def get_performance_trends(self, operation_name: str, 
                             days_back: int = 30) -> Dict[str, Any]:
        """Get performance trends for an operation."""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Filter measurements for this operation and time period
        relevant_measurements = [
            m for m in self._measurements
            if (m.operation_name == operation_name and 
                m.success and
                datetime.fromisoformat(m.timestamp) >= cutoff_date)
        ]
        
        if not relevant_measurements:
            return {"error": f"No measurements found for {operation_name} in last {days_back} days"}
        
        durations = [m.duration for m in relevant_measurements]
        
        # Calculate trend statistics
        trend_data = {
            "operation_name": operation_name,
            "measurement_count": len(durations),
            "time_period_days": days_back,
            "mean_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0.0,
            "min_duration": min(durations),
            "max_duration": max(durations),
            "recent_measurements": durations[-10:],  # Last 10 measurements
        }
        
        # Calculate trend direction (simple linear regression)
        if len(durations) >= 3:
            x_values = list(range(len(durations)))
            n = len(durations)
            sum_x = sum(x_values)
            sum_y = sum(durations)
            sum_xy = sum(x * y for x, y in zip(x_values, durations))
            sum_x2 = sum(x * x for x in x_values)
            
            # Linear regression slope
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            trend_data["trend_slope"] = slope
            trend_data["trend_direction"] = "improving" if slope < 0 else "degrading" if slope > 0 else "stable"
        else:
            trend_data["trend_slope"] = 0.0
            trend_data["trend_direction"] = "insufficient_data"
        
        return trend_data
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system_config": asdict(PerformanceUtils.get_system_capabilities()),
            "baselines": {},
            "trends": {},
            "summary": {
                "total_baselines": len(self._baselines),
                "total_measurements": len(self._measurements),
                "operations_tracked": len(set(m.operation_name for m in self._measurements))
            }
        }
        
        # Add baseline information
        for key, baseline in self._baselines.items():
            report["baselines"][baseline.operation_name] = {
                "baseline_time": baseline.baseline_time,
                "std_deviation": baseline.std_deviation,
                "confidence_interval": baseline.confidence_interval,
                "sample_count": baseline.sample_count,
                "created_at": baseline.created_at,
                "last_updated": baseline.last_updated
            }
        
        # Add trend information for each operation
        operations = set(baseline.operation_name for baseline in self._baselines.values())
        for operation in operations:
            report["trends"][operation] = self.get_performance_trends(operation)
        
        return report