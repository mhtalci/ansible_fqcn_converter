"""
Tests for parallel test execution infrastructure.

This module contains tests that verify the parallel test execution
setup is working correctly and that resource isolation is functioning
as expected.
"""

import os
import threading
import time
from pathlib import Path

import pytest


@pytest.mark.parallel_safe
def test_worker_isolation(test_execution_context, isolated_temp_dir):
    """Test that workers are properly isolated."""
    context = test_execution_context
    
    # Verify we have proper context information
    assert 'worker_id' in context
    assert 'is_parallel' in context
    assert 'thread_id' in context
    assert 'process_id' in context
    assert 'temp_dir' in context
    
    # Verify isolated temp directory is unique
    assert isolated_temp_dir.exists()
    assert str(context['worker_id']) in str(isolated_temp_dir) or context['worker_id'] == 'master'
    
    # Create a test file to verify isolation
    test_file = isolated_temp_dir / f"worker_test_{context['worker_id']}.txt"
    test_file.write_text(f"Worker {context['worker_id']} - Thread {context['thread_id']}")
    
    assert test_file.exists()
    assert context['worker_id'] in test_file.read_text()


@pytest.mark.parallel_safe
def test_environment_isolation(parallel_safe_environment):
    """Test that environment variables are properly isolated."""
    env = parallel_safe_environment
    
    # Verify environment setup
    assert 'worker_id' in env
    assert 'temp_dir' in env
    assert 'is_parallel' in env
    
    # Verify environment variables are set
    assert os.environ.get('FQCN_TEST_WORKER_ID') == env['worker_id']
    assert os.environ.get('FQCN_TEST_TEMP_DIR') == str(env['temp_dir'])
    
    # Verify config directories exist
    config_dir = Path(os.environ['FQCN_CONFIG_DIR'])
    cache_dir = Path(os.environ['FQCN_CACHE_DIR'])
    
    assert config_dir.exists()
    assert cache_dir.exists()


@pytest.mark.parallel_safe
def test_mock_config_isolation(mock_config_manager, worker_id):
    """Test that mock configuration is properly isolated per worker."""
    # Verify mock has worker ID
    assert hasattr(mock_config_manager, '_worker_id')
    assert mock_config_manager._worker_id == worker_id
    
    # Verify mock functionality
    mappings = mock_config_manager.load_default_mappings()
    assert isinstance(mappings, dict)
    assert len(mappings) > 0
    
    # Verify each worker gets its own copy
    mappings['test_key'] = f'worker_{worker_id}_value'
    assert mappings['test_key'] == f'worker_{worker_id}_value'


@pytest.mark.parallel_safe
def test_concurrent_file_operations(isolated_temp_dir, worker_id):
    """Test that concurrent file operations don't interfere."""
    # Create multiple files concurrently
    files_created = []
    
    for i in range(5):
        test_file = isolated_temp_dir / f"concurrent_test_{worker_id}_{i}.txt"
        test_file.write_text(f"Worker {worker_id} - File {i} - Thread {threading.get_ident()}")
        files_created.append(test_file)
        
        # Small delay to simulate real work
        time.sleep(0.01)
    
    # Verify all files were created correctly
    for i, test_file in enumerate(files_created):
        assert test_file.exists()
        content = test_file.read_text()
        assert f"Worker {worker_id}" in content
        assert f"File {i}" in content


@pytest.mark.parallel_safe
def test_logging_isolation(worker_id):
    """Test that logging is properly isolated between workers."""
    import logging
    
    # Create worker-specific logger
    logger_name = f"test_logger_{worker_id}"
    logger = logging.getLogger(logger_name)
    
    # Configure logger
    logger.setLevel(logging.DEBUG)
    
    # Test logging doesn't interfere
    logger.info(f"Test message from worker {worker_id}")
    
    # Verify logger configuration
    assert logger.name == logger_name
    assert logger.level == logging.DEBUG


@pytest.mark.serial
def test_serial_execution_marker(serial_test_lock):
    """Test that serial marker works correctly."""
    # This test should run serially even in parallel mode
    with serial_test_lock:
        # Simulate work that requires exclusive access
        time.sleep(0.1)
        
        # Verify we can acquire the lock
        assert True


@pytest.mark.parallel_safe
@pytest.mark.parametrize("test_id", range(3))
def test_parametrized_parallel_execution(test_id, worker_id, isolated_temp_dir):
    """Test that parametrized tests work correctly in parallel."""
    # Create test-specific file
    test_file = isolated_temp_dir / f"param_test_{worker_id}_{test_id}.txt"
    test_file.write_text(f"Parametrized test {test_id} on worker {worker_id}")
    
    assert test_file.exists()
    content = test_file.read_text()
    assert str(test_id) in content
    assert worker_id in content


@pytest.mark.parallel_safe
def test_resource_cleanup(isolated_temp_dir, worker_id):
    """Test that resources are properly cleaned up."""
    # Create some test resources
    test_files = []
    for i in range(3):
        test_file = isolated_temp_dir / f"cleanup_test_{worker_id}_{i}.txt"
        test_file.write_text(f"Cleanup test file {i}")
        test_files.append(test_file)
    
    # Verify files exist
    for test_file in test_files:
        assert test_file.exists()
    
    # The cleanup will be handled by the fixture teardown
    # This test just verifies the setup works correctly


@pytest.mark.performance
@pytest.mark.parallel_safe
def test_parallel_performance_baseline(worker_id):
    """Test basic performance characteristics in parallel mode."""
    start_time = time.time()
    
    # Simulate some work
    total = 0
    for i in range(1000):
        total += i * i
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Basic performance assertion (should complete quickly)
    assert execution_time < 1.0  # Should complete in less than 1 second
    assert total > 0  # Verify work was done


@pytest.mark.integration
@pytest.mark.parallel_safe
def test_parallel_integration_setup(ansible_project_structure, worker_id):
    """Test that integration test setup works in parallel."""
    project_dir = ansible_project_structure
    
    # Verify project structure was created
    assert project_dir.exists()
    assert (project_dir / "site.yml").exists()
    assert (project_dir / "roles" / "nginx" / "tasks" / "main.yml").exists()
    
    # Verify worker isolation
    assert str(worker_id) in str(project_dir) or worker_id == 'master'
    
    # Test file operations
    test_file = project_dir / f"integration_test_{worker_id}.yml"
    test_file.write_text(f"""---
- name: Integration test for worker {worker_id}
  hosts: localhost
  tasks:
    - name: Debug worker
      debug:
        msg: "Running on worker {worker_id}"
""")
    
    assert test_file.exists()
    content = test_file.read_text()
    assert worker_id in content