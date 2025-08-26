"""
Performance tests for validation engine.

Tests the performance characteristics of the validation engine
with various file sizes and complexity levels.
"""

import time

import pytest

from fqcn_converter.core.validator import ValidationEngine
from tests.fixtures.data_generators import PlaybookGenerator


@pytest.mark.performance
class TestValidationPerformance:
    """Test validation performance with various file sizes."""

    @pytest.mark.parametrize("num_tasks", [50, 100, 200, 500])
    def test_validation_time_scaling(self, tmp_path, num_tasks):
        """Test that validation time scales reasonably with file size."""
        generator = PlaybookGenerator()
        content = generator.generate_simple_playbook(num_tasks=num_tasks)
        test_file = tmp_path / f"validation_test_{num_tasks}.yml"
        test_file.write_text(content)

        validator = ValidationEngine()
        
        start_time = time.time()
        result = validator.validate_conversion(test_file)
        duration = time.time() - start_time

        # Validation should be fast - allow 0.1s per 100 tasks
        max_expected_time = (num_tasks / 100) * 0.1
        assert duration < max_expected_time, f"Validation of {num_tasks} tasks took {duration:.2f}s, expected < {max_expected_time:.2f}s"
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

        # Concurrent should be faster or comparable
        assert concurrent_time <= sequential_time * 1.1, f"Concurrent validation ({concurrent_time:.2f}s) should be faster than sequential ({sequential_time:.2f}s)"
        assert len(results) == len(sequential_results) == len(files)