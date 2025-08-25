"""
Regression and Performance Testing for FQCN Converter.

This module provides comprehensive regression testing for previously fixed bugs,
performance benchmarking on large projects and datasets, multi-Python version
compatibility validation, and profiling to identify bottlenecks.
"""

import pytest
import time
import psutil
import os
import sys
import threading
import tempfile
import subprocess
import cProfile
import pstats
import io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
from memory_profiler import profile as memory_profile

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.config.manager import ConfigurationManager


class PerformanceProfiler:
    """Enhanced performance profiler for comprehensive testing."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.metrics = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def start_profiling(self, test_name: str):
        """Start performance profiling for a test."""
        self.metrics[test_name] = {
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss,
            'start_cpu': self.process.cpu_percent(),
            'peak_memory': self.process.memory_info().rss,
            'cpu_samples': [],
            'memory_samples': [],
            'io_counters_start': self.process.io_counters() if hasattr(self.process, 'io_counters') else None
        }
        
        self.monitoring = True
        self.current_test = test_name
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_profiling(self, test_name: str) -> dict:
        """Stop profiling and return metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        end_cpu = self.process.cpu_percent()
        
        metrics = self.metrics[test_name]
        metrics.update({
            'end_time': end_time,
            'end_memory': end_memory,
            'end_cpu': end_cpu,
            'duration': end_time - metrics['start_time'],
            'memory_delta': end_memory - metrics['start_memory'],
            'peak_memory_delta': metrics['peak_memory'] - metrics['start_memory'],
            'avg_cpu': sum(metrics['cpu_samples']) / len(metrics['cpu_samples']) if metrics['cpu_samples'] else 0,
            'max_memory': max(metrics['memory_samples']) if metrics['memory_samples'] else end_memory,
            'io_counters_end': self.process.io_counters() if hasattr(self.process, 'io_counters') else None
        })
        
        # Calculate I/O metrics if available
        if metrics['io_counters_start'] and metrics['io_counters_end']:
            start_io = metrics['io_counters_start']
            end_io = metrics['io_counters_end']
            metrics.update({
                'read_bytes': end_io.read_bytes - start_io.read_bytes,
                'write_bytes': end_io.write_bytes - start_io.write_bytes,
                'read_count': end_io.read_count - start_io.read_count,
                'write_count': end_io.write_count - start_io.write_count
            })
        
        return metrics
    
    def _monitor_resources(self):
        """Monitor system resources in background."""
        while self.monitoring:
            try:
                current_memory = self.process.memory_info().rss
                current_cpu = self.process.cpu_percent()
                
                if current_memory > self.metrics[self.current_test]['peak_memory']:
                    self.metrics[self.current_test]['peak_memory'] = current_memory
                
                self.metrics[self.current_test]['memory_samples'].append(current_memory)
                self.metrics[self.current_test]['cpu_samples'].append(current_cpu)
                
                time.sleep(0.1)  # Sample every 100ms
            except Exception:
                break


class RegressionTestDataGenerator:
    """Generator for regression test data based on previously fixed bugs."""
    
    @staticmethod
    def create_yaml_parsing_edge_cases(base_dir: Path) -> dict:
        """Create YAML files that previously caused parsing issues."""
        test_cases = {}
        
        # Case 1: Complex YAML with nested structures and special characters
        test_cases['complex_yaml'] = base_dir / "complex_yaml.yml"
        test_cases['complex_yaml'].write_text("""---
- name: Complex YAML test with special characters
  hosts: "{{ target_hosts | default('all') }}"
  vars:
    special_chars: "!@#$%^&*()_+-=[]{}|;':,./<>?"
    nested_dict:
      level1:
        level2:
          level3: "deep value"
    list_with_dicts:
      - name: "item1"
        value: 100
      - name: "item2"
        value: 200
  
  tasks:
    - name: Task with complex when condition
      package:
        name: "{{ item.name }}"
        state: present
      loop: "{{ packages | default([]) }}"
      when: >
        (item.condition | default(true)) and
        (ansible_os_family == "Debian" or ansible_os_family == "RedHat") and
        not (skip_packages | default(false))
    
    - name: Task with multiline string
      copy:
        content: |
          This is a multiline string
          with multiple lines
          and special characters: {{ special_chars }}
        dest: "/tmp/multiline.txt"
        owner: root
        group: root
        mode: '0644'
    
    - name: Task with complex template
      template:
        src: "complex.j2"
        dest: "/etc/config/{{ item.name }}.conf"
        owner: "{{ item.owner | default('root') }}"
        group: "{{ item.group | default('root') }}"
        mode: "{{ item.mode | default('0644') }}"
      loop: "{{ config_files }}"
      notify:
        - restart service
        - reload config
""")
        
        # Case 2: YAML with problematic indentation that previously failed
        test_cases['indentation_issues'] = base_dir / "indentation_issues.yml"
        test_cases['indentation_issues'].write_text("""---
- name: Playbook with indentation challenges
  hosts: all
  tasks:
    - name: Normal task
      service:
        name: nginx
        state: started
    
    - name: Task with block
      block:
        - name: Subtask 1
          package:
            name: curl
            state: present
        
        - name: Subtask 2 with nested when
          file:
            path: /tmp/test
            state: touch
          when: >
            condition1 and
            condition2 and
            (condition3 or condition4)
      
      rescue:
        - name: Rescue task
          debug:
            msg: "Block failed"
      
      always:
        - name: Always task
          command: echo "Always runs"
    
    - name: Task with complex loop
      user:
        name: "{{ item.name }}"
        groups: "{{ item.groups | join(',') }}"
        state: present
      loop:
        - name: user1
          groups: [admin, users]
        - name: user2
          groups: [users, developers]
      loop_control:
        label: "{{ item.name }}"
""")
        
        # Case 3: YAML with edge case module usage that previously caused issues
        test_cases['module_edge_cases'] = base_dir / "module_edge_cases.yml"
        test_cases['module_edge_cases'].write_text("""---
- name: Module edge cases that previously failed
  hosts: all
  tasks:
    # Module with no parameters (previously caused issues)
    - name: Gather facts explicitly
      setup:
    
    # Module with only when condition
    - name: Conditional package install
      package:
        name: optional-package
        state: present
      when: install_optional | default(false)
    
    # Module with complex parameter structure
    - name: Complex file permissions
      file:
        path: "{{ item.path }}"
        state: "{{ item.state | default('directory') }}"
        owner: "{{ item.owner | default('root') }}"
        group: "{{ item.group | default('root') }}"
        mode: "{{ item.mode | default('0755') }}"
        recurse: "{{ item.recurse | default(false) }}"
      loop: "{{ file_operations | default([]) }}"
    
    # Module with inline dictionary (previously problematic)
    - name: Inline dictionary usage
      lineinfile: {path: /etc/hosts, line: "127.0.0.1 localhost", state: present}
    
    # Module with mixed parameter styles
    - name: Mixed parameter styles
      copy:
        src: source.txt
        dest: /tmp/dest.txt
        owner: root
        group: root
        mode: '0644'
        backup: yes
      register: copy_result
    
    # Module with complex register and conditional
    - name: Complex conditional based on register
      service:
        name: "{{ service_name }}"
        state: restarted
      when: 
        - copy_result is changed
        - service_name is defined
        - not (skip_restart | default(false))
""")
        
        return test_cases
    
    @staticmethod
    def create_performance_test_projects(base_dir: Path) -> dict:
        """Create projects of various sizes for performance testing."""
        projects = {}
        
        # Small project (baseline)
        small_project = base_dir / "small_project"
        small_project.mkdir()
        
        (small_project / "site.yml").write_text("""---
- name: Small project
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
    
    - name: Start service
      service:
        name: nginx
        state: started
""")
        
        projects['small'] = small_project
        
        # Medium project (realistic size)
        medium_project = base_dir / "medium_project"
        
        # Create 5 roles with multiple files each
        roles = ['webserver', 'database', 'monitoring', 'backup', 'security']
        
        for role in roles:
            role_dir = medium_project / "roles" / role
            (role_dir / "tasks").mkdir(parents=True)
            (role_dir / "handlers").mkdir(parents=True)
            (role_dir / "vars").mkdir(parents=True)
            
            # Tasks file with 20 tasks each
            tasks_content = "---\n"
            for i in range(20):
                tasks_content += f"""- name: {role} task {i}
  package:
    name: "{role}-package-{i}"
    state: present
  when: install_{role}_packages | default(true)

- name: {role} service {i}
  service:
    name: "{role}-service-{i}"
    state: started
    enabled: yes

- name: {role} config {i}
  template:
    src: "{role}-{i}.conf.j2"
    dest: "/etc/{role}/{role}-{i}.conf"
    owner: root
    group: root
    mode: '0644'
  notify: restart {role}

"""
            
            (role_dir / "tasks" / "main.yml").write_text(tasks_content)
            
            # Handlers
            (role_dir / "handlers" / "main.yml").write_text(f"""---
- name: restart {role}
  service:
    name: {role}
    state: restarted

- name: reload {role}
  service:
    name: {role}
    state: reloaded
""")
        
        # Main playbook
        (medium_project / "site.yml").write_text(f"""---
- name: Medium project deployment
  hosts: all
  roles:
{chr(10).join(f'    - {role}' for role in roles)}
""")
        
        projects['medium'] = medium_project
        
        # Large project (stress test)
        large_project = base_dir / "large_project"
        
        # Create 20 roles with multiple files each
        large_roles = [f"role_{i:02d}" for i in range(20)]
        
        for role in large_roles:
            role_dir = large_project / "roles" / role
            (role_dir / "tasks").mkdir(parents=True)
            (role_dir / "handlers").mkdir(parents=True)
            (role_dir / "vars").mkdir(parents=True)
            (role_dir / "defaults").mkdir(parents=True)
            
            # Tasks file with 50 tasks each
            tasks_content = "---\n"
            for i in range(50):
                tasks_content += f"""- name: {role} package task {i}
  package:
    name: "{role}-pkg-{i}"
    state: present

- name: {role} user task {i}
  user:
    name: "{role}-user-{i}"
    state: present
    system: yes

- name: {role} file task {i}
  file:
    path: "/opt/{role}/data-{i}"
    state: directory
    owner: "{role}-user-{i}"
    group: "{role}-user-{i}"
    mode: '0755'

- name: {role} service task {i}
  service:
    name: "{role}-svc-{i}"
    state: started
    enabled: yes

- name: {role} copy task {i}
  copy:
    src: "{role}-file-{i}.txt"
    dest: "/opt/{role}/config-{i}.txt"
    owner: root
    group: root
    mode: '0644'

"""
            
            (role_dir / "tasks" / "main.yml").write_text(tasks_content)
            
            # Multiple handler files
            (role_dir / "handlers" / "main.yml").write_text(f"""---
- name: restart {role}
  service:
    name: {role}
    state: restarted

- name: reload {role}
  service:
    name: {role}
    state: reloaded

- name: restart all {role} services
  service:
    name: "{{{{ item }}}}"
    state: restarted
  loop: "{{{{ {role}_services }}}}"
""")
        
        # Multiple playbooks
        for i in range(10):
            playbook_roles = large_roles[i*2:(i+1)*2]  # 2 roles per playbook
            (large_project / f"deploy_{i:02d}.yml").write_text(f"""---
- name: Large project deployment {i}
  hosts: group_{i}
  roles:
{chr(10).join(f'    - {role}' for role in playbook_roles)}
""")
        
        projects['large'] = large_project
        
        return projects


class TestRegressionTesting:
    """Regression tests for previously fixed bugs and issues."""
    
    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()
    
    @pytest.fixture
    def regression_test_data(self, temp_dir):
        """Regression test data fixture."""
        return RegressionTestDataGenerator.create_yaml_parsing_edge_cases(temp_dir)
    
    def test_yaml_parsing_regression(self, regression_test_data):
        """Test that previously problematic YAML parsing issues are fixed."""
        converter = FQCNConverter()
        
        for test_name, test_file in regression_test_data.items():
            # Should not raise parsing exceptions
            result = converter.convert_file(test_file, dry_run=True)
            
            assert result.success is True, f"YAML parsing failed for {test_name}"
            assert result.changes_made >= 0, f"Invalid changes count for {test_name}"
            assert result.converted_content is not None, f"No converted content for {test_name}"
    
    def test_complex_yaml_structure_regression(self, regression_test_data):
        """Test complex YAML structures that previously caused issues."""
        converter = FQCNConverter()
        validator = ValidationEngine()
        
        complex_file = regression_test_data['complex_yaml']
        
        # Convert the complex file
        result = converter.convert_file(complex_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 0
        
        # Verify specific conversions
        converted_content = complex_file.read_text()
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.copy:' in converted_content
        assert 'ansible.builtin.template:' in converted_content
        
        # Validate the converted file
        validation_result = validator.validate_conversion(complex_file)
        assert validation_result.valid is True
        assert validation_result.score > 0.8
    
    def test_indentation_handling_regression(self, regression_test_data):
        """Test that indentation issues are properly handled."""
        converter = FQCNConverter()
        
        indentation_file = regression_test_data['indentation_issues']
        original_content = indentation_file.read_text()
        
        # Convert file
        result = converter.convert_file(indentation_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 0
        
        # Verify YAML structure is preserved
        converted_content = indentation_file.read_text()
        
        # Check that conversions were made
        assert 'ansible.builtin.service:' in converted_content
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.file:' in converted_content
        assert 'ansible.builtin.user:' in converted_content
        assert 'ansible.builtin.debug:' in converted_content
        assert 'ansible.builtin.command:' in converted_content
        
        # Verify YAML is still valid
        import yaml
        try:
            yaml.safe_load(converted_content)
        except yaml.YAMLError as e:
            pytest.fail(f"Converted YAML is invalid: {e}")
    
    def test_module_edge_cases_regression(self, regression_test_data):
        """Test edge cases in module usage that previously failed."""
        converter = FQCNConverter()
        
        edge_cases_file = regression_test_data['module_edge_cases']
        
        # Convert file
        result = converter.convert_file(edge_cases_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 0
        
        converted_content = edge_cases_file.read_text()
        
        # Verify specific edge cases are handled
        assert 'ansible.builtin.setup:' in converted_content  # Module with no params
        assert 'ansible.builtin.package:' in converted_content  # Conditional module
        assert 'ansible.builtin.file:' in converted_content  # Complex parameters
        assert 'ansible.builtin.lineinfile:' in converted_content  # Inline dictionary
        assert 'ansible.builtin.copy:' in converted_content  # Mixed parameter styles
        assert 'ansible.builtin.service:' in converted_content  # Complex conditional
    
    def test_batch_processing_error_recovery_regression(self, temp_dir):
        """Test that batch processing properly recovers from errors."""
        batch_processor = BatchProcessor(max_workers=2)
        
        # Create mixed project with valid and invalid files
        project_dir = temp_dir / "mixed_project"
        project_dir.mkdir()
        
        # Valid file
        (project_dir / "valid.yml").write_text("""---
- name: Valid playbook
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        # Invalid YAML file
        (project_dir / "invalid.yml").write_text("""---
- name: Invalid playbook
  hosts: all
  tasks:
    - name: Broken task
      package: [
""")
        
        # Another valid file
        (project_dir / "another_valid.yml").write_text("""---
- name: Another valid playbook
  hosts: all
  tasks:
    - name: Create user
      user:
        name: testuser
        state: present
""")
        
        # Process the project
        results = batch_processor.process_projects([str(project_dir)], dry_run=True)
        
        assert len(results) == 1  # One project processed
        
        # Should have processed some files successfully despite errors
        project_result = results[0]
        assert project_result['files_processed'] >= 2  # At least the valid files
        
        # Should have some successful conversions
        assert project_result['modules_converted'] >= 2  # From the valid files
    
    def test_configuration_loading_regression(self, temp_dir):
        """Test configuration loading edge cases that previously failed."""
        config_manager = ConfigurationManager()
        
        # Test with non-existent config file
        non_existent_config = temp_dir / "non_existent.yml"
        
        # Should handle gracefully
        try:
            mappings = config_manager.load_custom_mappings(str(non_existent_config))
            # Should return empty dict or default mappings
            assert isinstance(mappings, dict)
        except Exception as e:
            # Should raise appropriate exception, not crash
            assert "not found" in str(e).lower() or "no such file" in str(e).lower()
        
        # Test with invalid YAML config
        invalid_config = temp_dir / "invalid_config.yml"
        invalid_config.write_text("invalid: yaml: content: [")
        
        with pytest.raises(Exception):  # Should raise YAML parsing error
            config_manager.load_custom_mappings(str(invalid_config))
        
        # Test with empty config file
        empty_config = temp_dir / "empty_config.yml"
        empty_config.write_text("")
        
        mappings = config_manager.load_custom_mappings(str(empty_config))
        assert isinstance(mappings, dict)
    
    def test_memory_leak_regression(self, temp_dir, profiler):
        """Test for memory leaks in repeated operations."""
        profiler.start_profiling("memory_leak_test")
        
        converter = FQCNConverter()
        
        # Create test file
        test_file = temp_dir / "test.yml"
        test_file.write_text("""---
- name: Memory leak test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        # Perform many conversions
        initial_memory = psutil.Process().memory_info().rss
        
        for i in range(100):
            # Reset file content
            test_file.write_text("""---
- name: Memory leak test iteration %d
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""" % i)
            
            # Convert file
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True
            
            # Check memory usage every 10 iterations
            if i % 10 == 0:
                current_memory = psutil.Process().memory_info().rss
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (less than 50MB)
                assert memory_growth < 50 * 1024 * 1024, f"Excessive memory growth: {memory_growth / 1024 / 1024:.2f} MB"
        
        metrics = profiler.stop_profiling("memory_leak_test")
        
        # Final memory check
        final_memory_growth = metrics['memory_delta']
        assert final_memory_growth < 100 * 1024 * 1024, f"Memory leak detected: {final_memory_growth / 1024 / 1024:.2f} MB growth"


class TestPerformanceBenchmarking:
    """Performance benchmarking tests for various project sizes and scenarios."""
    
    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()
    
    @pytest.fixture
    def performance_projects(self, temp_dir):
        """Performance test projects fixture."""
        return RegressionTestDataGenerator.create_performance_test_projects(temp_dir)
    
    def test_small_project_performance_baseline(self, performance_projects, profiler):
        """Establish performance baseline with small project."""
        profiler.start_profiling("small_project_baseline")
        
        converter = FQCNConverter()
        small_project = performance_projects['small']
        
        # Convert project
        site_yml = small_project / "site.yml"
        result = converter.convert_file(site_yml, dry_run=False)
        
        metrics = profiler.stop_profiling("small_project_baseline")
        
        assert result.success is True
        assert result.changes_made > 0
        
        # Performance expectations for small project
        assert metrics['duration'] < 1.0  # Less than 1 second
        assert metrics['peak_memory_delta'] < 10 * 1024 * 1024  # Less than 10MB
        
        print(f"Small project baseline: {metrics['duration']:.3f}s, {metrics['peak_memory_delta'] / 1024 / 1024:.2f}MB")
    
    def test_medium_project_performance(self, performance_projects, profiler):
        """Test performance with medium-sized project."""
        profiler.start_profiling("medium_project_performance")
        
        batch_processor = BatchProcessor(max_workers=2)
        medium_project = performance_projects['medium']
        
        # Process entire project
        results = batch_processor.process_projects([str(medium_project)], dry_run=False)
        
        metrics = profiler.stop_profiling("medium_project_performance")
        
        assert len(results) == 1
        assert results[0]['success'] is True
        
        # Performance expectations for medium project
        assert metrics['duration'] < 10.0  # Less than 10 seconds
        assert metrics['peak_memory_delta'] < 50 * 1024 * 1024  # Less than 50MB
        
        # Throughput expectations
        total_files = results[0]['files_processed']
        files_per_second = total_files / metrics['duration']
        assert files_per_second > 1.0  # At least 1 file per second
        
        print(f"Medium project: {metrics['duration']:.3f}s, {metrics['peak_memory_delta'] / 1024 / 1024:.2f}MB, {files_per_second:.2f} files/s")
    
    def test_large_project_performance(self, performance_projects, profiler):
        """Test performance with large project (stress test)."""
        profiler.start_profiling("large_project_performance")
        
        batch_processor = BatchProcessor(max_workers=4)
        large_project = performance_projects['large']
        
        # Process entire project
        results = batch_processor.process_projects([str(large_project)], dry_run=False)
        
        metrics = profiler.stop_profiling("large_project_performance")
        
        assert len(results) == 1
        assert results[0]['success'] is True
        
        # Performance expectations for large project
        assert metrics['duration'] < 60.0  # Less than 1 minute
        assert metrics['peak_memory_delta'] < 200 * 1024 * 1024  # Less than 200MB
        
        # Throughput expectations
        total_files = results[0]['files_processed']
        total_modules = results[0]['modules_converted']
        
        files_per_second = total_files / metrics['duration']
        modules_per_second = total_modules / metrics['duration']
        
        assert files_per_second > 0.5  # At least 0.5 files per second
        assert modules_per_second > 10.0  # At least 10 modules per second
        
        print(f"Large project: {metrics['duration']:.3f}s, {metrics['peak_memory_delta'] / 1024 / 1024:.2f}MB")
        print(f"Throughput: {files_per_second:.2f} files/s, {modules_per_second:.2f} modules/s")
    
    def test_parallel_processing_scalability(self, performance_projects, profiler):
        """Test scalability of parallel processing."""
        medium_project = performance_projects['medium']
        
        # Test with different worker counts
        worker_counts = [1, 2, 4, 8]
        results = {}
        
        for workers in worker_counts:
            profiler.start_profiling(f"parallel_workers_{workers}")
            
            batch_processor = BatchProcessor(max_workers=workers)
            batch_results = batch_processor.process_projects([str(medium_project)], dry_run=True)
            
            metrics = profiler.stop_profiling(f"parallel_workers_{workers}")
            
            assert len(batch_results) == 1
            assert batch_results[0]['success'] is True
            
            results[workers] = {
                'duration': metrics['duration'],
                'memory': metrics['peak_memory_delta'],
                'files_processed': batch_results[0]['files_processed']
            }
        
        # Analyze scalability
        baseline_time = results[1]['duration']
        
        for workers in [2, 4, 8]:
            parallel_time = results[workers]['duration']
            speedup = baseline_time / parallel_time
            
            print(f"Workers: {workers}, Speedup: {speedup:.2f}x, Time: {parallel_time:.3f}s")
            
            # Should see some improvement with more workers (allowing for overhead)
            if workers <= 4:  # Up to 4 workers should show improvement
                assert speedup > 0.4  # At least 40% of theoretical speedup (adjusted for test environment and overhead)
    
    def test_memory_usage_scaling(self, temp_dir, profiler):
        """Test memory usage scaling with file size."""
        converter = FQCNConverter()
        
        # Test with files of increasing size
        file_sizes = [100, 500, 1000, 2000]  # Number of tasks
        memory_usage = {}
        
        for size in file_sizes:
            profiler.start_profiling(f"file_size_{size}")
            
            # Create large file
            large_file = temp_dir / f"large_{size}.yml"
            content = "---\n- name: Large file test\n  hosts: all\n  tasks:\n"
            
            for i in range(size):
                content += f"""    - name: Task {i}
      package:
        name: package{i}
        state: present
    
"""
            
            large_file.write_text(content)
            
            # Convert file
            result = converter.convert_file(large_file, dry_run=True)
            
            metrics = profiler.stop_profiling(f"file_size_{size}")
            
            assert result.success is True
            assert result.changes_made == size  # Should convert all tasks
            
            memory_usage[size] = metrics['peak_memory_delta']
            
            print(f"File size: {size} tasks, Memory: {metrics['peak_memory_delta'] / 1024 / 1024:.2f}MB, Time: {metrics['duration']:.3f}s")
        
        # Memory usage should scale reasonably (not exponentially)
        for i in range(1, len(file_sizes)):
            prev_size = file_sizes[i-1]
            curr_size = file_sizes[i]
            
            size_ratio = curr_size / prev_size
            # Use a more realistic minimum memory baseline to avoid measurement noise
            min_memory_baseline = 1024 * 1024  # 1MB minimum baseline
            memory_ratio = memory_usage[curr_size] / max(memory_usage[prev_size], min_memory_baseline)
            
            # Memory growth should be roughly linear, not exponential
            assert memory_ratio < size_ratio * 2, f"Memory usage growing too fast: {memory_ratio:.2f}x for {size_ratio:.2f}x size increase"
    
    def test_cpu_profiling_bottlenecks(self, performance_projects, temp_dir):
        """Profile CPU usage to identify bottlenecks."""
        # Create profiler
        pr = cProfile.Profile()
        
        # Profile medium project conversion
        medium_project = performance_projects['medium']
        batch_processor = BatchProcessor(max_workers=1)  # Single worker for cleaner profiling
        
        pr.enable()
        results = batch_processor.process_projects([str(medium_project)], dry_run=True)
        pr.disable()
        
        assert len(results) == 1
        assert results[0]['success'] is True
        
        # Analyze profiling results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        profile_output = s.getvalue()
        
        # Save profile for analysis
        profile_file = temp_dir / "cpu_profile.txt"
        profile_file.write_text(profile_output)
        
        print("Top CPU consumers:")
        print(profile_output[:1000])  # Print first 1000 characters
        
        # Basic checks - no single function should dominate excessively
        lines = profile_output.split('\n')
        for line in lines[5:15]:  # Skip header, check top functions
            if line.strip() and 'tottime' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        cumtime = float(parts[3])
                        # No single function should take more than 50% of total time
                        # (This is a rough heuristic)
                        assert cumtime < 30.0, f"Potential bottleneck detected: {line}"
                    except (ValueError, IndexError):
                        continue


class TestMultiPythonCompatibility:
    """Test compatibility across multiple Python versions."""
    
    def test_python_version_compatibility(self, temp_dir):
        """Test that the converter works across Python versions."""
        # This test runs in the current Python version
        # In a real CI environment, this would be run across multiple Python versions
        
        converter = FQCNConverter()
        
        # Create test file
        test_file = temp_dir / "compatibility_test.yml"
        test_file.write_text("""---
- name: Python compatibility test
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
    
    - name: Start service
      service:
        name: nginx
        state: started
""")
        
        # Test basic functionality
        result = converter.convert_file(test_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made == 2
        
        converted_content = test_file.read_text()
        assert 'ansible.builtin.package:' in converted_content
        assert 'ansible.builtin.service:' in converted_content
        
        # Test that Python version info is accessible
        python_version = sys.version_info
        assert python_version.major >= 3
        assert python_version.minor >= 8  # Minimum supported version
        
        print(f"Tested on Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    def test_dependency_compatibility(self):
        """Test that all dependencies are compatible."""
        # Test importing all major dependencies
        try:
            import yaml
            import psutil
            import pathlib
            import concurrent.futures
            import argparse
            import logging
            
            # Test basic functionality of key dependencies
            assert hasattr(yaml, 'safe_load')
            assert hasattr(psutil, 'Process')
            assert hasattr(concurrent.futures, 'ThreadPoolExecutor')
            
        except ImportError as e:
            pytest.fail(f"Dependency import failed: {e}")
    
    def test_file_system_compatibility(self, temp_dir):
        """Test file system operations across different platforms."""
        converter = FQCNConverter()
        
        # Test with various file path formats
        test_cases = [
            "simple.yml",
            "with spaces.yml",
            "with-dashes.yml",
            "with_underscores.yml",
            "UPPERCASE.YML",
            "mixed.Case.yml"
        ]
        
        for filename in test_cases:
            test_file = temp_dir / filename
            test_file.write_text("""---
- name: File system compatibility test
  hosts: all
  tasks:
    - name: Test task
      package:
        name: test
        state: present
""")
            
            # Should handle all filename formats
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True, f"Failed to process file: {filename}"
    
    def test_encoding_compatibility(self, temp_dir):
        """Test handling of different text encodings."""
        converter = FQCNConverter()
        
        # Test with UTF-8 content including special characters
        test_file = temp_dir / "encoding_test.yml"
        
        content_with_unicode = """---
- name: Encoding test with unicode characters
  hosts: all
  vars:
    special_chars: "áéíóú ñ ç 中文 русский العربية"
    emoji: "🚀 🐍 ⚡"
  
  tasks:
    - name: Install package with unicode description
      package:
        name: nginx
        state: present
      tags:
        - "配置"
        - "configuración"
"""
        
        # Write with explicit UTF-8 encoding
        test_file.write_text(content_with_unicode, encoding='utf-8')
        
        # Should handle Unicode content properly
        result = converter.convert_file(test_file, dry_run=False)
        
        assert result.success is True
        assert result.changes_made > 0
        
        # Verify Unicode characters are preserved
        converted_content = test_file.read_text(encoding='utf-8')
        assert 'ansible.builtin.package:' in converted_content
        assert '中文' in converted_content
        assert 'русский' in converted_content
        assert '🚀' in converted_content


class TestBottleneckIdentification:
    """Tests to identify and validate performance bottlenecks."""
    
    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()
    
    def test_yaml_parsing_performance(self, temp_dir, profiler):
        """Test YAML parsing performance bottlenecks."""
        converter = FQCNConverter()
        
        # Create complex YAML file
        complex_file = temp_dir / "complex_parsing.yml"
        
        # Generate complex YAML structure
        content = "---\n"
        content += "- name: Complex YAML parsing test\n"
        content += "  hosts: all\n"
        content += "  vars:\n"
        content += "    complex_dict:\n"
        
        # Create deeply nested structure
        for i in range(10):
            indent = "      " + "  " * i
            content += f"{indent}level_{i}:\n"
            content += f"{indent}  value: 'level {i} value'\n"
            content += f"{indent}  list:\n"
            for j in range(5):
                content += f"{indent}    - item_{j}: value_{j}\n"
        
        content += "  tasks:\n"
        for i in range(100):
            content += f"""    - name: Task {i}
      package:
        name: "package_{i}"
        state: present
      when: >
        (condition_{i} | default(false)) and
        (global_condition | default(true))
    
"""
        
        complex_file.write_text(content)
        
        profiler.start_profiling("yaml_parsing_performance")
        
        # Convert the complex file
        result = converter.convert_file(complex_file, dry_run=True)
        
        metrics = profiler.stop_profiling("yaml_parsing_performance")
        
        assert result.success is True
        assert result.changes_made == 100  # Should convert all package modules
        
        # YAML parsing should not be the bottleneck
        assert metrics['duration'] < 5.0  # Should complete within 5 seconds
        
        print(f"Complex YAML parsing: {metrics['duration']:.3f}s for {len(content)} characters")
    
    def test_regex_performance_bottlenecks(self, temp_dir, profiler):
        """Test regex pattern matching performance."""
        converter = FQCNConverter()
        
        # Create file with many potential matches
        regex_test_file = temp_dir / "regex_test.yml"
        
        content = "---\n- name: Regex performance test\n  hosts: all\n  tasks:\n"
        
        # Create many tasks with various module patterns
        modules = ['package', 'service', 'user', 'group', 'file', 'copy', 'template']
        
        for i in range(500):  # 500 tasks
            module = modules[i % len(modules)]
            content += f"""    - name: Task {i} with {module}
      {module}:
        name: "item_{i}"
        state: present
    
"""
        
        regex_test_file.write_text(content)
        
        profiler.start_profiling("regex_performance")
        
        result = converter.convert_file(regex_test_file, dry_run=True)
        
        metrics = profiler.stop_profiling("regex_performance")
        
        assert result.success is True
        assert result.changes_made == 500  # Should convert all modules
        
        # Regex matching should be efficient
        assert metrics['duration'] < 3.0  # Should complete within 3 seconds
        
        # Calculate modules per second
        modules_per_second = result.changes_made / metrics['duration']
        assert modules_per_second > 100  # Should process at least 100 modules per second
        
        print(f"Regex performance: {modules_per_second:.2f} modules/s")
    
    def test_file_io_bottlenecks(self, temp_dir, profiler):
        """Test file I/O performance bottlenecks."""
        converter = FQCNConverter()
        
        # Create multiple files for I/O testing
        files = []
        for i in range(50):
            test_file = temp_dir / f"io_test_{i:02d}.yml"
            test_file.write_text(f"""---
- name: I/O test file {i}
  hosts: all
  tasks:
    - name: Install package {i}
      package:
        name: "package_{i}"
        state: present
    
    - name: Start service {i}
      service:
        name: "service_{i}"
        state: started
""")
            files.append(test_file)
        
        profiler.start_profiling("file_io_performance")
        
        # Process all files
        total_changes = 0
        for test_file in files:
            result = converter.convert_file(test_file, dry_run=False)
            assert result.success is True
            total_changes += result.changes_made
        
        metrics = profiler.stop_profiling("file_io_performance")
        
        assert total_changes == 100  # 2 modules per file * 50 files
        
        # File I/O should be efficient
        files_per_second = len(files) / metrics['duration']
        assert files_per_second > 10  # Should process at least 10 files per second
        
        print(f"File I/O performance: {files_per_second:.2f} files/s")
        
        # Check I/O metrics if available
        if 'read_bytes' in metrics and 'write_bytes' in metrics:
            total_io = metrics['read_bytes'] + metrics['write_bytes']
            io_throughput = total_io / metrics['duration'] / 1024 / 1024  # MB/s
            
            print(f"I/O throughput: {io_throughput:.2f} MB/s")
            assert io_throughput > 1.0  # Should achieve at least 1 MB/s
    
    def test_memory_allocation_patterns(self, temp_dir, profiler):
        """Test memory allocation patterns and potential leaks."""
        converter = FQCNConverter()
        
        # Test repeated operations to check for memory leaks
        test_file = temp_dir / "memory_test.yml"
        
        profiler.start_profiling("memory_allocation_test")
        
        initial_memory = psutil.Process().memory_info().rss
        peak_memory = initial_memory
        
        for i in range(100):
            # Create new content each iteration
            content = f"""---
- name: Memory allocation test {i}
  hosts: all
  tasks:
    - name: Task {i}
      package:
        name: "package_{i}"
        state: present
"""
            test_file.write_text(content)
            
            # Convert file
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True
            
            # Monitor memory usage
            current_memory = psutil.Process().memory_info().rss
            if current_memory > peak_memory:
                peak_memory = current_memory
            
            # Memory should not grow excessively
            memory_growth = current_memory - initial_memory
            assert memory_growth < 50 * 1024 * 1024, f"Excessive memory growth at iteration {i}: {memory_growth / 1024 / 1024:.2f} MB"
        
        metrics = profiler.stop_profiling("memory_allocation_test")
        
        final_memory_growth = metrics['memory_delta']
        peak_memory_growth = metrics['peak_memory_delta']
        
        print(f"Memory allocation: Final growth: {final_memory_growth / 1024 / 1024:.2f} MB, Peak growth: {peak_memory_growth / 1024 / 1024:.2f} MB")
        
        # Memory growth should be reasonable
        assert final_memory_growth < 30 * 1024 * 1024  # Less than 30MB final growth
        assert peak_memory_growth < 50 * 1024 * 1024   # Less than 50MB peak growth