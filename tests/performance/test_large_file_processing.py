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
        
        start_time = time.time()
        result = converter.convert_file(test_file)
        duration = time.time() - start_time

        # Performance assertions
        assert duration < 5.0, f"Large playbook conversion took {duration:.2f}s, expected < 5.0s"
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

    @pytest.mark.parametrize("num_tasks", [10, 50, 100, 200])
    def test_conversion_time_scaling(self, tmp_path, num_tasks):
        """Test that conversion time scales reasonably with file size."""
        generator = PlaybookGenerator()
        content = generator.generate_simple_playbook(num_tasks=num_tasks)
        test_file = tmp_path / f"playbook_{num_tasks}.yml"
        test_file.write_text(content)

        converter = FQCNConverter()
        
        start_time = time.time()
        result = converter.convert_file(test_file)
        duration = time.time() - start_time

        # Time should scale roughly linearly (allow some overhead)
        max_expected_time = (num_tasks / 10) * 0.5  # 0.5s per 10 tasks
        assert duration < max_expected_time, f"Conversion of {num_tasks} tasks took {duration:.2f}s, expected < {max_expected_time:.2f}s"
        assert result.success, f"Conversion of {num_tasks} tasks should succeed"


@pytest.mark.performance
class TestBatchProcessingPerformance:
    """Test performance of batch processing operations."""

    def test_parallel_vs_sequential_performance(self, tmp_path):
        """Test that parallel processing is faster than sequential."""
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

        # Parallel should be faster (or at least not significantly slower)
        assert parallel_time <= sequential_time * 1.2, f"Parallel ({parallel_time:.2f}s) should be faster than sequential ({sequential_time:.2f}s)"
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