"""
Configuration for pytest-xdist parallel test execution.

This module provides configuration and hooks for managing parallel test
execution with proper resource isolation and load balancing.
"""

import os
import tempfile
from pathlib import Path


def pytest_configure_node(node):
    """
    Configure each test worker node for parallel execution.
    
    This function is called for each worker node and sets up
    worker-specific configuration and resources.
    """
    # Get worker ID
    worker_id = getattr(node, 'workerinput', {}).get('workerid', 'master')
    
    # Create worker-specific temporary directory
    if worker_id != 'master':
        temp_base = Path(tempfile.gettempdir()) / f"fqcn_test_{worker_id}"
        temp_base.mkdir(exist_ok=True)
        
        # Set environment variables for the worker
        os.environ[f'FQCN_WORKER_{worker_id}_TEMP'] = str(temp_base)
        os.environ['FQCN_CURRENT_WORKER'] = worker_id


def pytest_runtest_setup(item):
    """
    Set up each test for parallel execution.
    
    This function is called before each test and ensures proper
    resource isolation and configuration.
    """
    # Check if test is marked as serial and handle accordingly
    if item.get_closest_marker('serial'):
        # For serial tests, we might want to use a global lock
        # This is handled in the conftest.py fixtures
        pass
    
    # Set up worker-specific logging
    worker_id = os.environ.get('FQCN_CURRENT_WORKER', 'master')
    if worker_id != 'master':
        import logging
        logger = logging.getLogger(f'fqcn_test_{worker_id}')
        logger.setLevel(logging.DEBUG)


def pytest_runtest_teardown(item, nextitem):
    """
    Clean up after each test in parallel execution.
    
    This function ensures proper cleanup of resources after each test.
    """
    # Clean up any worker-specific resources
    worker_id = os.environ.get('FQCN_CURRENT_WORKER', 'master')
    
    if worker_id != 'master':
        # Clean up worker-specific temporary files if needed
        temp_base = Path(tempfile.gettempdir()) / f"fqcn_test_{worker_id}"
        
        # Only clean up test-specific files, not the worker directory itself
        for temp_file in temp_base.glob('test_*'):
            if temp_file.is_file():
                temp_file.unlink(missing_ok=True)
            elif temp_file.is_dir():
                import shutil
                shutil.rmtree(temp_file, ignore_errors=True)


def pytest_sessionfinish(session, exitstatus):
    """
    Clean up after the entire test session.
    
    This function is called after all tests have completed and
    performs final cleanup of worker resources.
    """
    worker_id = os.environ.get('FQCN_CURRENT_WORKER', 'master')
    
    if worker_id != 'master':
        # Clean up worker-specific temporary directory
        temp_base = Path(tempfile.gettempdir()) / f"fqcn_test_{worker_id}"
        if temp_base.exists():
            import shutil
            shutil.rmtree(temp_base, ignore_errors=True)
        
        # Clean up environment variables
        env_vars_to_remove = [
            f'FQCN_WORKER_{worker_id}_TEMP',
            'FQCN_CURRENT_WORKER'
        ]
        
        for env_var in env_vars_to_remove:
            os.environ.pop(env_var, None)


# Note: Custom xdist hooks can be added here if needed
# For now, we use the default xdist behavior with our custom
# node configuration and resource management