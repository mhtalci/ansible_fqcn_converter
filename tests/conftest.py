"""
Pytest configuration and shared fixtures for FQCN Converter tests.

This module provides comprehensive fixtures and configuration for all test modules
to ensure consistent test setup and teardown, including support for parallel
test execution with proper resource isolation.

Enhanced Test Fixtures (Task 9 Implementation):
===============================================

1. isolated_temp_dir:
   - Provides worker-specific temporary directories for parallel execution
   - Ensures proper cleanup even on test failures
   - Cross-platform compatible with proper permissions
   - Requirements: 6.2, 4.1, 4.3

2. mock_config_manager:
   - Thread-safe configuration manager mocking
   - Worker-specific configuration isolation
   - Realistic default behavior with error simulation capabilities
   - Integration with test environment setup
   - Requirements: 6.4, 4.1, 4.4

3. test_environment_setup:
   - Comprehensive test environment configuration
   - Worker-specific environment variables
   - Platform-independent settings
   - Proper resource management and cleanup
   - Requirements: 6.1, 6.2, 6.3, 6.4, 6.5

4. resource_cleanup_tracker:
   - Tracks and ensures cleanup of test resources
   - Handles files, directories, processes, and threads
   - Essential for parallel execution safety
   - Requirements: 6.5, 4.4

5. platform_compatibility:
   - Platform-specific compatibility utilities
   - Cross-platform path and file handling
   - Consistent behavior across operating systems
   - Requirements: 6.3

All fixtures are designed to work together seamlessly and support both
sequential and parallel test execution modes.
"""

import os
import shutil
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import performance monitoring plugin
pytest_plugins = ["tests.fixtures.pytest_performance_plugin"]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def isolated_temp_dir(worker_id):
    """
    Create an isolated temporary directory for parallel test execution.
    
    This fixture ensures each test worker gets its own isolated temporary
    directory to prevent resource conflicts during parallel execution.
    
    Features:
    - Worker-specific directory naming
    - Proper cleanup even on test failures
    - Cross-platform compatibility
    - Thread-safe operation
    
    Requirements: 6.2, 4.1, 4.3
    """
    import threading
    import time
    
    # Create worker-specific temporary directory with timestamp for uniqueness
    timestamp = int(time.time() * 1000000)  # microsecond precision
    thread_id = threading.get_ident()
    
    if worker_id == "master":
        # Running in non-parallel mode
        temp_dir = tempfile.mkdtemp(
            prefix=f"fqcn_test_{timestamp}_{thread_id}_",
            suffix="_master"
        )
    else:
        # Running in parallel mode - create worker-specific directory
        temp_dir = tempfile.mkdtemp(
            prefix=f"fqcn_test_{timestamp}_{thread_id}_",
            suffix=f"_{worker_id}"
        )
    
    temp_path = Path(temp_dir)
    
    # Ensure directory has proper permissions
    temp_path.chmod(0o755)
    
    try:
        yield temp_path
    finally:
        # Ensure cleanup even if test fails
        # Use multiple attempts for Windows compatibility
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if temp_path.exists():
                    shutil.rmtree(temp_path, ignore_errors=False)
                break
            except (OSError, PermissionError) as e:
                if attempt == max_attempts - 1:
                    # Final attempt - use ignore_errors=True
                    shutil.rmtree(temp_path, ignore_errors=True)
                else:
                    # Wait a bit and retry (helps with Windows file locking)
                    time.sleep(0.1)


@pytest.fixture
def worker_id(request):
    """
    Get the worker ID for parallel test execution.
    
    Returns 'master' if running in non-parallel mode, or the worker ID
    (e.g., 'gw0', 'gw1') if running in parallel mode.
    """
    if hasattr(request.config, 'workerinput'):
        return request.config.workerinput['workerid']
    return "master"


@pytest.fixture
def sample_playbook_content():
    """Sample Ansible playbook content for testing."""
    return """---
- name: Test playbook
  hosts: all
  become: yes
  
  vars:
    nginx_port: 80
    user_name: testuser
  
  pre_tasks:
    - name: Update package cache
      package:
        update_cache: yes
  
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Copy nginx config
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
        owner: root
        group: root
        mode: '0644'
      notify: restart nginx
    
    - name: Create nginx user
      user:
        name: nginx
        system: yes
        shell: /bin/false
        home: /var/lib/nginx
        create_home: no
    
    - name: Start and enable nginx
      service:
        name: nginx
        state: started
        enabled: yes
    
    - name: Debug message
      debug:
        msg: "Nginx installation completed"
  
  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
  
  post_tasks:
    - name: Set deployment fact
      set_fact:
        deployment_complete: true
        deployment_time: "{{ ansible_date_time.iso8601 }}"
"""


@pytest.fixture
def sample_task_file_content():
    """Sample Ansible task file content for testing."""
    return """---
- name: Create application directory
  file:
    path: /opt/myapp
    state: directory
    owner: root
    group: root
    mode: '0755'

- name: Template application config
  template:
    src: app.conf.j2
    dest: /opt/myapp/app.conf
    owner: myapp
    group: myapp
    mode: '0640'

- name: Install application packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - python3
    - python3-pip
    - python3-venv

- name: Run application setup command
  command: /opt/myapp/setup.sh
  args:
    creates: /opt/myapp/.setup_complete

- name: Create systemd service file
  copy:
    content: |
      [Unit]
      Description=My Application
      After=network.target
      
      [Service]
      Type=simple
      User=myapp
      Group=myapp
      ExecStart=/opt/myapp/start.sh
      Restart=always
      
      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/myapp.service
    owner: root
    group: root
    mode: '0644'
  notify: reload systemd

- name: Enable and start myapp service
  service:
    name: myapp
    enabled: yes
    state: started
"""


@pytest.fixture
def sample_converted_content():
    """Sample converted Ansible content for validation testing."""
    return """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Start service
      ansible.builtin.service:
        name: nginx
        state: started
    
    - name: Create user
      ansible.builtin.user:
        name: testuser
        state: present
"""


@pytest.fixture
def sample_fqcn_mappings():
    """Sample FQCN mappings for testing."""
    return {
        # Ansible builtin modules
        "copy": "ansible.builtin.copy",
        "file": "ansible.builtin.file",
        "template": "ansible.builtin.template",
        "service": "ansible.builtin.service",
        "systemd": "ansible.builtin.systemd",
        "user": "ansible.builtin.user",
        "group": "ansible.builtin.group",
        "package": "ansible.builtin.package",
        "apt": "ansible.builtin.apt",
        "yum": "ansible.builtin.yum",
        "command": "ansible.builtin.command",
        "shell": "ansible.builtin.shell",
        "debug": "ansible.builtin.debug",
        "set_fact": "ansible.builtin.set_fact",
        "include_tasks": "ansible.builtin.include_tasks",
        "import_tasks": "ansible.builtin.import_tasks",
        "mount": "ansible.builtin.mount",
        "cron": "ansible.builtin.cron",
        "lineinfile": "ansible.builtin.lineinfile",
        "replace": "ansible.builtin.replace",
        # Community modules
        "docker_container": "community.docker.docker_container",
        "docker_image": "community.docker.docker_image",
        "mysql_user": "community.mysql.mysql_user",
        "mysql_db": "community.mysql.mysql_db",
        "postgresql_user": "community.postgresql.postgresql_user",
        "postgresql_db": "community.postgresql.postgresql_db",
        "git": "ansible.builtin.git",
        "unarchive": "ansible.builtin.unarchive",
    }


@pytest.fixture
def mock_config_manager(sample_fqcn_mappings, worker_id, test_environment_setup):
    """
    Mock ConfigurationManager for testing with parallel execution support.
    
    This fixture creates a thread-safe mock that works correctly in
    parallel test execution environments with consistent configuration.
    
    Features:
    - Thread-safe operation
    - Worker-specific configuration isolation
    - Realistic default behavior
    - Proper error simulation capabilities
    - Integration with test environment setup
    
    Requirements: 6.4, 4.1, 4.4
    """
    with patch("fqcn_converter.config.manager.ConfigurationManager") as mock_class:
        mock_instance = Mock()
        
        # Create thread-safe copies of mappings for each worker
        worker_mappings = sample_fqcn_mappings.copy()
        
        # Configure realistic mock behavior
        mock_instance.load_default_mappings.return_value = worker_mappings
        mock_instance.load_custom_mappings.return_value = {}
        mock_instance.merge_mappings.return_value = worker_mappings
        mock_instance.get_mapping.side_effect = lambda key: worker_mappings.get(key)
        mock_instance.has_mapping.side_effect = lambda key: key in worker_mappings
        
        # Add configuration file paths from test environment
        mock_instance.config_dir = test_environment_setup['config_dir']
        mock_instance.cache_dir = test_environment_setup['cache_dir']
        
        # Add worker ID and environment info for debugging parallel issues
        mock_instance._worker_id = worker_id
        mock_instance._test_env = test_environment_setup
        mock_instance._is_parallel = test_environment_setup['is_parallel']
        
        # Add methods for error simulation in tests
        def simulate_config_error():
            from fqcn_converter.exceptions import ConfigurationError
            raise ConfigurationError("Simulated configuration error")
        
        def simulate_file_error():
            from fqcn_converter.exceptions import FileAccessError
            raise FileAccessError("Simulated file access error")
        
        mock_instance.simulate_config_error = simulate_config_error
        mock_instance.simulate_file_error = simulate_file_error
        
        # Configure the class to return our mock instance
        mock_class.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def test_environment_setup(worker_id, isolated_temp_dir):
    """
    Set up a comprehensive test environment for consistent testing.
    
    This fixture provides:
    - Isolated temporary directories per worker
    - Worker-specific environment variables
    - Proper cleanup and resource management
    - Platform-independent configuration
    - Parallel execution safety
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    # Store original environment
    original_env = os.environ.copy()
    
    # Set worker-specific environment variables
    test_env = {
        'FQCN_TEST_WORKER_ID': worker_id,
        'FQCN_TEST_TEMP_DIR': str(isolated_temp_dir),
        'FQCN_TEST_MODE': 'parallel' if worker_id != 'master' else 'sequential',
        # Prevent tests from interfering with user's actual config
        'FQCN_CONFIG_DIR': str(isolated_temp_dir / 'config'),
        'FQCN_CACHE_DIR': str(isolated_temp_dir / 'cache'),
        'FQCN_LOG_DIR': str(isolated_temp_dir / 'logs'),
        # Disable user config loading during tests
        'FQCN_DISABLE_USER_CONFIG': '1',
        # Set consistent locale for cross-platform testing
        'LC_ALL': 'C.UTF-8',
        'LANG': 'C.UTF-8',
    }
    
    # Apply test environment
    os.environ.update(test_env)
    
    # Create necessary directories with proper permissions
    config_dir = isolated_temp_dir / 'config'
    cache_dir = isolated_temp_dir / 'cache'
    log_dir = isolated_temp_dir / 'logs'
    
    config_dir.mkdir(exist_ok=True, mode=0o755)
    cache_dir.mkdir(exist_ok=True, mode=0o755)
    log_dir.mkdir(exist_ok=True, mode=0o755)
    
    # Create default config files for testing
    default_config = config_dir / 'fqcn_mapping.yml'
    default_config.write_text("""---
# Default test configuration
copy: ansible.builtin.copy
file: ansible.builtin.file
service: ansible.builtin.service
""")
    
    environment_info = {
        'worker_id': worker_id,
        'temp_dir': isolated_temp_dir,
        'config_dir': config_dir,
        'cache_dir': cache_dir,
        'log_dir': log_dir,
        'is_parallel': worker_id != 'master',
        'original_env': original_env,
    }
    
    try:
        yield environment_info
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
def parallel_safe_environment(test_environment_setup):
    """
    Alias for test_environment_setup for backward compatibility.
    
    This fixture maintains compatibility with existing tests while
    providing the enhanced test environment setup functionality.
    """
    return test_environment_setup


@pytest.fixture
def ansible_project_structure(isolated_temp_dir):
    """
    Create a complete Ansible project structure for testing.
    
    Uses isolated_temp_dir to ensure parallel test safety.
    """
    project_dir = isolated_temp_dir / "test_project"

    # Create directory structure
    (project_dir / "group_vars").mkdir(parents=True)
    (project_dir / "host_vars").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "tasks").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "handlers").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "templates").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "vars").mkdir(parents=True)
    (project_dir / "roles" / "nginx" / "defaults").mkdir(parents=True)

    # Create playbook files
    (project_dir / "site.yml").write_text(
        """---
- name: Main site playbook
  hosts: all
  roles:
    - nginx
"""
    )

    (project_dir / "webservers.yml").write_text(
        """---
- name: Configure web servers
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
"""
    )

    # Create role files
    (project_dir / "roles" / "nginx" / "tasks" / "main.yml").write_text(
        """---
- name: Install nginx
  package:
    name: nginx
    state: present

- name: Start nginx
  service:
    name: nginx
    state: started
"""
    )

    (project_dir / "roles" / "nginx" / "handlers" / "main.yml").write_text(
        """---
- name: restart nginx
  service:
    name: nginx
    state: restarted
"""
    )

    # Create inventory
    (project_dir / "inventory.ini").write_text(
        """[webservers]
web1.example.com
web2.example.com

[databases]
db1.example.com
"""
    )

    return project_dir


@pytest.fixture(autouse=True)
def reset_logging(worker_id):
    """
    Reset logging configuration after each test with parallel execution support.
    
    This fixture ensures logging doesn't interfere between parallel test workers.
    """
    import logging
    
    # Create worker-specific logger name to avoid conflicts
    logger_name = f"fqcn_converter_test_{worker_id}"
    
    yield
    
    # Reset logging to avoid interference between tests
    # Clear all handlers for the worker-specific logger
    worker_logger = logging.getLogger(logger_name)
    worker_logger.handlers.clear()
    worker_logger.setLevel(logging.WARNING)
    
    # Also clean up the main logger
    main_logger = logging.getLogger()
    main_logger.handlers.clear()
    main_logger.setLevel(logging.WARNING)


# Global lock for tests that cannot run in parallel
_SERIAL_TEST_LOCK = threading.Lock()


@pytest.fixture
def serial_test_lock():
    """
    Provide a lock for tests that must run serially.
    
    Use this fixture for tests that cannot safely run in parallel,
    such as tests that modify global state or use exclusive resources.
    """
    return _SERIAL_TEST_LOCK


@pytest.fixture
def test_execution_context(worker_id, parallel_safe_environment):
    """
    Provide comprehensive test execution context information.
    
    This fixture provides information about the current test execution
    environment, useful for debugging parallel execution issues.
    """
    context = {
        'worker_id': worker_id,
        'is_parallel': worker_id != 'master',
        'thread_id': threading.get_ident(),
        'process_id': os.getpid(),
        'temp_dir': parallel_safe_environment['temp_dir'],
    }
    
    return context


@pytest.fixture
def cli_args():
    """Factory fixture for creating CLI argument objects."""

    def _create_args(**kwargs):
        """Create an argparse.Namespace object with default CLI arguments."""
        defaults = {
            "verbosity": "normal",
            "files": ["test.yml"],
            "config": None,
            "dry_run": False,
            "backup": False,
            "no_backup": False,
            "progress": False,
            "report": None,
            "skip_validation": False,
            "lint": False,
            "force": False,
            "exclude": None,
        }
        defaults.update(kwargs)

        from argparse import Namespace

        return Namespace(**defaults)

    return _create_args


@pytest.fixture
def resource_cleanup_tracker():
    """
    Track and ensure cleanup of test resources.
    
    This fixture helps ensure that all test resources are properly
    cleaned up, which is especially important for parallel execution.
    
    Requirements: 6.5, 4.4
    """
    resources = {
        'temp_files': [],
        'temp_dirs': [],
        'open_files': [],
        'processes': [],
        'threads': [],
    }
    
    def register_temp_file(self, file_path):
        """Register a temporary file for cleanup."""
        resources['temp_files'].append(Path(file_path))
    
    def register_temp_dir(self, dir_path):
        """Register a temporary directory for cleanup."""
        resources['temp_dirs'].append(Path(dir_path))
    
    def register_open_file(self, file_obj):
        """Register an open file object for cleanup."""
        resources['open_files'].append(file_obj)
    
    def register_process(self, process):
        """Register a process for cleanup."""
        resources['processes'].append(process)
    
    def register_thread(self, thread):
        """Register a thread for cleanup."""
        resources['threads'].append(thread)
    
    cleanup_tracker = type('ResourceCleanupTracker', (), {
        'register_temp_file': register_temp_file,
        'register_temp_dir': register_temp_dir,
        'register_open_file': register_open_file,
        'register_process': register_process,
        'register_thread': register_thread,
        'resources': resources,
    })()
    
    try:
        yield cleanup_tracker
    finally:
        # Clean up all registered resources
        
        # Close open files
        for file_obj in resources['open_files']:
            try:
                if hasattr(file_obj, 'close') and not file_obj.closed:
                    file_obj.close()
            except Exception:
                pass
        
        # Terminate processes
        for process in resources['processes']:
            try:
                if hasattr(process, 'terminate'):
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                pass
        
        # Join threads
        for thread in resources['threads']:
            try:
                if hasattr(thread, 'join') and thread.is_alive():
                    thread.join(timeout=5)
            except Exception:
                pass
        
        # Remove temporary files
        for temp_file in resources['temp_files']:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass
        
        # Remove temporary directories
        for temp_dir in resources['temp_dirs']:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


@pytest.fixture
def platform_compatibility():
    """
    Provide platform-specific compatibility information and utilities.
    
    This fixture helps tests account for platform differences and
    ensures consistent behavior across different operating systems.
    
    Requirements: 6.3
    """
    import platform
    import sys
    
    system_info = {
        'platform': platform.system().lower(),
        'is_windows': platform.system().lower() == 'windows',
        'is_linux': platform.system().lower() == 'linux',
        'is_macos': platform.system().lower() == 'darwin',
        'python_version': sys.version_info,
        'path_separator': os.sep,
        'line_separator': os.linesep,
    }
    
    def get_executable_extension():
        """Get the executable file extension for the current platform."""
        return '.exe' if system_info['is_windows'] else ''
    
    def get_temp_dir():
        """Get the appropriate temporary directory for the platform."""
        return Path(tempfile.gettempdir())
    
    def normalize_path(path):
        """Normalize a path for the current platform."""
        return Path(path).resolve()
    
    def get_line_ending():
        """Get the appropriate line ending for the platform."""
        return '\r\n' if system_info['is_windows'] else '\n'
    
    compatibility = type('PlatformCompatibility', (), {
        **system_info,
        'get_executable_extension': get_executable_extension,
        'get_temp_dir': get_temp_dir,
        'normalize_path': normalize_path,
        'get_line_ending': get_line_ending,
    })()
    
    return compatibility
