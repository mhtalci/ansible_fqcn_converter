"""
Performance testing utilities for adaptive timing and system capability detection.

This module provides utilities to detect system capabilities and adjust
performance test expectations accordingly.
"""

import psutil
import time
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class SystemCapabilities:
    """System capability information for performance testing."""
    cpu_cores: int
    memory_gb: float
    cpu_speed_factor: float
    io_speed_factor: float


class PerformanceUtils:
    """Utilities for adaptive performance testing."""
    
    _system_capabilities: SystemCapabilities = None
    _baseline_measurements: Dict[str, float] = {}
    
    @classmethod
    def get_system_capabilities(cls) -> SystemCapabilities:
        """Get system capabilities with caching."""
        if cls._system_capabilities is None:
            cls._system_capabilities = cls._measure_system_capabilities()
        return cls._system_capabilities
    
    @classmethod
    def _measure_system_capabilities(cls) -> SystemCapabilities:
        """Measure system capabilities for performance scaling."""
        cpu_cores = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Measure CPU speed factor with a simple benchmark
        cpu_speed_factor = cls._measure_cpu_speed()
        
        # Measure I/O speed factor with a simple file operation
        io_speed_factor = cls._measure_io_speed()
        
        return SystemCapabilities(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            cpu_speed_factor=cpu_speed_factor,
            io_speed_factor=io_speed_factor
        )
    
    @classmethod
    def _measure_cpu_speed(cls) -> float:
        """Measure relative CPU speed factor (1.0 = baseline)."""
        # Simple CPU benchmark - calculate primes
        start_time = time.time()
        primes = []
        for num in range(2, 1000):
            for i in range(2, int(num ** 0.5) + 1):
                if num % i == 0:
                    break
            else:
                primes.append(num)
        duration = time.time() - start_time
        
        # Baseline expectation: ~0.01s on modern hardware
        baseline_time = 0.01
        return baseline_time / max(duration, 0.001)  # Avoid division by zero
    
    @classmethod
    def _measure_io_speed(cls) -> float:
        """Measure relative I/O speed factor (1.0 = baseline)."""
        import tempfile
        import os
        
        # Simple I/O benchmark - write and read a file
        test_data = "x" * 10000  # 10KB test data
        
        start_time = time.time()
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
            f.write(test_data)
        
        with open(temp_path, 'r') as f:
            read_data = f.read()
        
        os.unlink(temp_path)
        duration = time.time() - start_time
        
        # Baseline expectation: ~0.001s on modern SSD
        baseline_time = 0.001
        return baseline_time / max(duration, 0.0001)  # Avoid division by zero
    
    @classmethod
    def get_adaptive_timeout(cls, base_timeout: float, operation_type: str = "cpu") -> float:
        """Get adaptive timeout based on system capabilities."""
        capabilities = cls.get_system_capabilities()
        
        if operation_type == "cpu":
            # Scale based on CPU speed and core count
            factor = capabilities.cpu_speed_factor
            # More cores can help with parallel operations
            if capabilities.cpu_cores >= 8:
                factor *= 1.2
            elif capabilities.cpu_cores <= 2:
                factor *= 0.8
        elif operation_type == "io":
            # Scale based on I/O speed
            factor = capabilities.io_speed_factor
        else:
            # Mixed operations - use average of CPU and I/O factors
            factor = (capabilities.cpu_speed_factor + capabilities.io_speed_factor) / 2
        
        # Apply tolerance margin (20% buffer)
        adaptive_timeout = base_timeout / factor * 1.2
        
        # Ensure minimum reasonable timeout
        return max(adaptive_timeout, base_timeout * 0.5)
    
    @classmethod
    def get_performance_multiplier(cls, num_items: int, base_time_per_item: float) -> float:
        """Get performance multiplier based on system capabilities and item count."""
        capabilities = cls.get_system_capabilities()
        
        # Base multiplier from system capabilities
        cpu_multiplier = 1.0 / capabilities.cpu_speed_factor
        io_multiplier = 1.0 / capabilities.io_speed_factor
        
        # Average the multipliers for mixed workloads
        base_multiplier = (cpu_multiplier + io_multiplier) / 2
        
        # Scale factor based on number of items (larger datasets may be less efficient)
        if num_items > 200:
            scale_factor = 1.3  # 30% overhead for large datasets
        elif num_items > 100:
            scale_factor = 1.2  # 20% overhead for medium datasets
        else:
            scale_factor = 1.1  # 10% overhead for small datasets
        
        return base_multiplier * scale_factor
    
    @classmethod
    def assert_performance_within_tolerance(cls, actual_time: float, expected_time: float, 
                                          tolerance_factor: float = 1.5, 
                                          operation_type: str = "mixed") -> None:
        """Assert that performance is within acceptable tolerance."""
        adaptive_expected = cls.get_adaptive_timeout(expected_time, operation_type)
        max_allowed_time = adaptive_expected * tolerance_factor
        
        assert actual_time <= max_allowed_time, (
            f"Performance test failed: actual time {actual_time:.3f}s exceeds "
            f"adaptive expected time {adaptive_expected:.3f}s * tolerance {tolerance_factor} = "
            f"{max_allowed_time:.3f}s. System capabilities: {cls.get_system_capabilities()}"
        )
    
    @classmethod
    def get_parallel_efficiency_threshold(cls) -> float:
        """Get expected parallel efficiency threshold based on system capabilities."""
        capabilities = cls.get_system_capabilities()
        
        # For small workloads, parallel processing often has overhead
        # Threshold represents the maximum ratio of parallel_time/sequential_time
        if capabilities.cpu_cores >= 8:
            return 2.0  # Allow parallel to be up to 100% slower (overhead for small tasks)
        elif capabilities.cpu_cores >= 4:
            return 2.2  # Allow parallel to be up to 120% slower
        else:
            return 2.5  # Allow parallel to be up to 150% slower on low-core systems
    
    @classmethod
    def establish_performance_baselines(cls) -> None:
        """Establish performance baselines for common operations."""
        # Import here to avoid circular imports
        from .performance_monitor import get_performance_monitor
        from fqcn_converter.core.converter import FQCNConverter
        from fqcn_converter.core.validator import ValidationEngine
        from tests.fixtures.data_generators import PlaybookGenerator
        import tempfile
        import os
        
        monitor = get_performance_monitor()
        generator = PlaybookGenerator()
        
        print("Establishing performance baselines...")
        
        # Baseline for file conversion
        def convert_file_test(num_tasks=50):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                content = generator.generate_simple_playbook(num_tasks=num_tasks)
                f.write(content)
                temp_path = f.name
            
            try:
                converter = FQCNConverter()
                converter.convert_file(temp_path)
            finally:
                os.unlink(temp_path)
        
        # Baseline for validation
        def validate_file_test(num_tasks=50):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                content = generator.generate_simple_playbook(num_tasks=num_tasks)
                f.write(content)
                temp_path = f.name
            
            try:
                validator = ValidationEngine()
                validator.validate_conversion(temp_path)
            finally:
                os.unlink(temp_path)
        
        # Establish baselines with different parameter sets
        conversion_params = [
            {"num_tasks": 10},
            {"num_tasks": 50},
            {"num_tasks": 100}
        ]
        
        validation_params = [
            {"num_tasks": 10},
            {"num_tasks": 50},
            {"num_tasks": 100}
        ]
        
        try:
            monitor.establish_baseline_for_function(
                convert_file_test, "file_conversion", conversion_params, min_samples=3
            )
            
            monitor.establish_baseline_for_function(
                validate_file_test, "file_validation", validation_params, min_samples=3
            )
            
            print("Performance baselines established successfully")
        except Exception as e:
            print(f"Warning: Could not establish all baselines: {e}")
    
    @classmethod
    def generate_performance_report(cls) -> Dict[str, any]:
        """Generate comprehensive performance report."""
        # Import here to avoid circular imports
        from .performance_reporter import PerformanceReporter
        reporter = PerformanceReporter()
        return reporter.generate_comprehensive_report()