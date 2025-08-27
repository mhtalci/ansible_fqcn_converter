"""
Performance tests for validation engine.

Tests the performance characteristics of the validation engine
with various file sizes and complexity levels.
"""

import time

import pytest

from fqcn_converter.core.validator import ValidationEngine
from tests.fixtures.data_generators import PlaybookGenerator
from tests.fixtures.performance_utils import PerformanceUtils


@pytest.mark.performance
class TestValidationPerformance:
    """Test validation performance with various file sizes."""

    @pytest.mark.parametrize("num_tasks,base_time_per_100", [
        (50, 0.8),    # Realistic: 0.8s per 100 tasks
        (100, 0.8),   # Linear scaling baseline
        (200, 0.8),   # Should scale linearly
        (500, 0.8),   # May have some overhead
    ])
    def test_validation_time_scaling(self, tmp_path, num_tasks, base_time_per_100):
        """Test that validation time scales reasonably with file size."""
        generator = PlaybookGenerator()
        content = generator.generate_simple_playbook(num_tasks=num_tasks)
        test_file = tmp_path / f"validation_test_{num_tasks}.yml"
        test_file.write_text(content)

        validator = ValidationEngine()
        
        start_time = time.time()
        result = validator.validate_conversion(test_file)
        duration = time.time() - start_time

        # Calculate expected time with performance multiplier
        base_expected_time = (num_tasks / 100) * base_time_per_100
        performance_multiplier = PerformanceUtils.get_performance_multiplier(num_tasks, base_time_per_100 / 100)
        expected_time = base_expected_time * performance_multiplier
        
        # Use adaptive performance assertion with tolerance
        PerformanceUtils.assert_performance_within_tolerance(
            actual_time=duration,
            expected_time=expected_time,
            tolerance_factor=4.0,  # Allow 4x tolerance for validation operations (can be highly variable)
            operation_type="mixed"
        )
        assert result is not None, "Validation should return a result"

    def test_validation_memory_efficiency(self, tmp_path):
        """Test that validation doesn't consume excessive memory."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        validator = ValidationEngine()
        generator = PlaybookGenerator()
        
        # Validate many files
        for i in range(20):
            content = generator.generate_simple_playbook(num_tasks=100)
            test_file = tmp_path / f"validation_file_{i}.yml"
            test_file.write_text(content)
            validator.validate_conversion(test_file)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable
        assert memory_growth < 100, f"Validation memory grew by {memory_growth:.1f}MB, expected < 100MB"

    def test_concurrent_validation_performance(self, tmp_path):
        """Test performance of concurrent validation operations."""
        import concurrent.futures
        
        # Create test files
        files = []
        generator = PlaybookGenerator()
        for i in range(10):
            content = generator.generate_simple_playbook(num_tasks=50)
            test_file = tmp_path / f"concurrent_test_{i}.yml"
            test_file.write_text(content)
            files.append(test_file)

        validator = ValidationEngine()

        def validate_file(file_path):
            return validator.validate_conversion(file_path)

        # Test concurrent validation
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(validate_file, f) for f in files]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        concurrent_time = time.time() - start_time

        # Test sequential validation
        start_time = time.time()
        sequential_results = [validate_file(f) for f in files]
        sequential_time = time.time() - start_time

        # Concurrent should be reasonable compared to sequential (allow for overhead)
        efficiency_threshold = PerformanceUtils.get_parallel_efficiency_threshold()
        max_allowed_concurrent_time = sequential_time * efficiency_threshold
        
        assert concurrent_time <= max_allowed_concurrent_time, (
            f"Concurrent validation efficiency below expectations: "
            f"concurrent ({concurrent_time:.2f}s) vs sequential ({sequential_time:.2f}s), "
            f"efficiency ratio: {concurrent_time/sequential_time:.2f}, "
            f"max allowed ratio: {efficiency_threshold:.1f}"
        )
        assert len(results) == len(sequential_results) == len(files)