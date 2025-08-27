"""
Performance tests for FQCN Converter.

Tests the performance characteristics of the converter with large files
and complex Ansible structures.
"""

import time
from pathlib import Path

import pytest

from fqcn_converter.core.converter import FQCNConverter
from tests.fixtures.data_generators import PlaybookGenerator
from tests.fixtures.performance_utils import PerformanceUtils
from tests.fixtures.performance_monitor import monitor_performance, measure_operation


@pytest.mark.performance
class TestLargeFileProcessing:
    """Test performance with large Ansible files."""

    def test_large_playbook_conversion_performance(self, tmp_path):
        """Test conversion performance with large playbooks."""
        # Generate a large playbook with 100 tasks
        generator = PlaybookGenerator()
        large_content = generator.generate_simple_playbook(num_tasks=100)
        test_file = tmp_path / "large_playbook.yml"
        test_file.write_text(large_content)

        converter = FQCNConverter()
        
        # Use performance monitoring context manager
        with measure_operation("large_playbook_conversion", 
                             parameters={"num_tasks": 100, "file_size": len(large_content)},
                             tolerance_factor=2.0):
            result = converter.convert_file(test_file)

        assert result.success, "Large playbook conversion should succeed"
        assert result.changes_made > 0, "Should make changes in large playbook"

    def test_memory_usage_large_files(self, tmp_path):
        """Test memory usage doesn't grow excessively with large files."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple large files
        converter = FQCNConverter()
        generator = PlaybookGenerator()
        for i in range(10):
            content = generator.generate_simple_playbook(num_tasks=50)
            test_file = tmp_path / f"playbook_{i}.yml"
            test_file.write_text(content)
            converter.convert_file(test_file)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (less than 100MB for this test)
        assert memory_growth < 100, f"Memory grew by {memory_growth:.1f}MB, expected < 100MB"

    @pytest.mark.parametrize("num_tasks,base_time_per_10", [
        (10, 0.8),    # Realistic: 0.8s per 10 tasks
        (50, 0.8),    # Should scale linearly
        (100, 0.8),   # Linear scaling baseline
        (200, 0.8),   # May have some overhead
    ])
    def test_conversion_time_scaling(self, tmp_path, num_tasks, base_time_per_10):
        """Test that conversion time scales reasonably with file size."""
        generator = PlaybookGenerator()
        content = generator.generate_simple_playbook(num_tasks=num_tasks)
        test_file = tmp_path / f"playbook_{num_tasks}.yml"
        test_file.write_text(content)

        converter = FQCNConverter()
        
        start_time = time.time()
        result = converter.convert_file(test_file)
        duration = time.time() - start_time

        # Calculate expected time with performance multiplier
        base_expected_time = (num_tasks / 10) * base_time_per_10
        performance_multiplier = PerformanceUtils.get_performance_multiplier(num_tasks, base_time_per_10 / 10)
        expected_time = base_expected_time * performance_multiplier
        
        # Use adaptive performance assertion with tolerance
        PerformanceUtils.assert_performance_within_tolerance(
            actual_time=duration,
            expected_time=expected_time,
            tolerance_factor=1.8,  # Allow 1.8x tolerance for conversion operations
            operation_type="mixed"
        )
        assert result.success, f"Conversion of {num_tasks} tasks should succeed"


@pytest.mark.performance
class TestBatchProcessingPerformance:
    """Test performance of batch processing operations."""

    def test_parallel_vs_sequential_performance(self, tmp_path):
        """Test that parallel processing efficiency meets system expectations."""
        # Create multiple test files
        files = []
        generator = PlaybookGenerator()
        for i in range(5):
            content = generator.generate_simple_playbook(num_tasks=20)
            test_file = tmp_path / f"playbook_{i}.yml"
            test_file.write_text(content)
            files.append(test_file)

        # For this test, we'll just test individual file processing speed
        # since BatchProcessor works with projects, not individual files
        converter = FQCNConverter()

        # Test sequential processing
        start_time = time.time()
        sequential_results = []
        for file_path in files:
            result = converter.convert_file(file_path)
            sequential_results.append(result)
        sequential_time = time.time() - start_time

        # Test parallel processing using ThreadPoolExecutor
        import concurrent.futures
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            parallel_results = list(executor.map(converter.convert_file, files))
        parallel_time = time.time() - start_time

        # Get adaptive parallel efficiency threshold based on system capabilities
        efficiency_threshold = PerformanceUtils.get_parallel_efficiency_threshold()
        max_allowed_parallel_time = sequential_time * efficiency_threshold
        
        # Calculate efficiency ratio for better reporting
        efficiency_ratio = parallel_time / sequential_time if sequential_time > 0 else float('inf')
        
        # Parallel should meet efficiency expectations for the system
        assert parallel_time <= max_allowed_parallel_time, (
            f"Parallel processing efficiency below expectations: "
            f"parallel ({parallel_time:.2f}s) vs sequential ({sequential_time:.2f}s), "
            f"efficiency ratio: {efficiency_ratio:.2f}, max allowed ratio: {efficiency_threshold:.1f}, "
            f"system: {PerformanceUtils.get_system_capabilities()}"
        )
        assert len(sequential_results) == len(parallel_results) == len(files)
        assert all(r.success for r in sequential_results)
        assert all(r.success for r in parallel_results)


@pytest.mark.performance
class TestMemoryEfficiency:
    """Test memory efficiency of the converter."""

    def test_memory_cleanup_after_conversion(self, tmp_path):
        """Test that memory is properly cleaned up after conversions."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process many files
        converter = FQCNConverter()
        generator = PlaybookGenerator()
        for i in range(20):
            content = generator.generate_simple_playbook(num_tasks=30)
            test_file = tmp_path / f"temp_playbook_{i}.yml"
            test_file.write_text(content)
            converter.convert_file(test_file)
            test_file.unlink()  # Clean up file

        # Force garbage collection
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_growth = final_memory - baseline_memory
        
        # Memory growth should be minimal after cleanup
        assert memory_growth < 50, f"Memory grew by {memory_growth:.1f}MB after cleanup, expected < 50MB"