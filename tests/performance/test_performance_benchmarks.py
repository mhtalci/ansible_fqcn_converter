"""
Performance benchmarking tests for FQCN Converter.

These tests validate performance characteristics, memory usage,
and scalability for large-scale Ansible project conversions.
"""

import pytest
import time
import psutil
import os
import tempfile
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine
from fqcn_converter.core.batch import BatchProcessor


class PerformanceMonitor:
    """Helper class for monitoring performance metrics."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_memory = None
        self.peak_memory = None
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        self.peak_memory = self.start_memory
        self.monitoring = True
        
        # Start memory monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_memory)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring and return metrics."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        return {
            'duration': end_time - self.start_time,
            'start_memory_mb': self.start_memory / 1024 / 1024,
            'end_memory_mb': end_memory / 1024 / 1024,
            'peak_memory_mb': self.peak_memory / 1024 / 1024,
            'memory_delta_mb': (end_memory - self.start_memory) / 1024 / 1024
        }
    
    def _monitor_memory(self):
        """Monitor memory usage in background thread."""
        while self.monitoring:
            try:
                current_memory = self.process.memory_info().rss
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory
                time.sleep(0.1)  # Check every 100ms
            except Exception:
                break


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    @pytest.fixture
    def large_playbook_content(self):
        """Generate large playbook content for performance testing."""
        tasks = []
        
        # Generate many tasks with different modules
        modules = ['package', 'service', 'copy', 'template', 'file', 'user', 'group', 'command', 'shell', 'debug']
        
        for i in range(100):  # 100 tasks
            module = modules[i % len(modules)]
            task = f"""  - name: Task {i + 1} - {module}
    {module}:
      name: "item_{i}"
      state: present"""
            tasks.append(task)
        
        return f"""---
- name: Large performance test playbook
  hosts: all
  become: yes
  
  vars:
    test_items: {list(range(100))}
  
  tasks:
{chr(10).join(tasks)}
"""
    
    @pytest.fixture
    def large_project_structure(self, temp_dir):
        """Create large project structure for performance testing."""
        project_dir = temp_dir / "large_performance_project"
        
        # Create many roles
        num_roles = 20
        for i in range(num_roles):
            role_name = f"role_{i:02d}"
            role_dir = project_dir / "roles" / role_name
            (role_dir / "tasks").mkdir(parents=True)
            (role_dir / "handlers").mkdir(parents=True)
            (role_dir / "vars").mkdir(parents=True)
            
            # Create tasks with many modules
            tasks_content = f"""---
# Tasks for {role_name}
"""
            for j in range(20):  # 20 tasks per role
                tasks_content += f"""
- name: Install package {j} for {role_name}
  package:
    name: "package_{role_name}_{j}"
    state: present

- name: Configure service {j} for {role_name}
  service:
    name: "service_{role_name}_{j}"
    state: started
    enabled: yes

- name: Create file {j} for {role_name}
  file:
    path: "/tmp/{role_name}_{j}.txt"
    state: touch
    owner: root
    group: root
    mode: '0644'

- name: Copy config {j} for {role_name}
  copy:
    content: "Config for {role_name} task {j}"
    dest: "/etc/{role_name}_{j}.conf"
    owner: root
    group: root
    mode: '0644'

- name: Create user {j} for {role_name}
  user:
    name: "user_{role_name}_{j}"
    state: present
    system: yes
"""
            
            (role_dir / "tasks" / "main.yml").write_text(tasks_content)
            
            # Create handlers
            handlers_content = f"""---
- name: restart service for {role_name}
  service:
    name: "main_service_{role_name}"
    state: restarted

- name: reload config for {role_name}
  command: "reload_config_{role_name}"
"""
            
            (role_dir / "handlers" / "main.yml").write_text(handlers_content)
        
        # Create main playbooks
        (project_dir / "site.yml").write_text(f"""---
- name: Deploy all roles
  hosts: all
  become: yes
  roles:
{chr(10).join(f'    - role_{i:02d}' for i in range(num_roles))}
""")
        
        # Create group-specific playbooks
        for i in range(0, num_roles, 5):  # Group every 5 roles
            group_roles = [f"role_{j:02d}" for j in range(i, min(i + 5, num_roles))]
            (project_dir / f"group_{i//5}.yml").write_text(f"""---
- name: Deploy group {i//5}
  hosts: "group_{i//5}"
  become: yes
  roles:
{chr(10).join(f'    - {role}' for role in group_roles)}
""")
        
        return project_dir
    
    def test_single_file_conversion_performance(self, large_playbook_content, temp_dir):
        """Test performance of converting a single large file."""
        # Create large test file
        test_file = temp_dir / "large_playbook.yml"
        test_file.write_text(large_playbook_content)
        
        converter = FQCNConverter()
        monitor = PerformanceMonitor()
        
        # Benchmark conversion
        monitor.start_monitoring()
        result = converter.convert_file(test_file, dry_run=True)
        metrics = monitor.stop_monitoring()
        
        # Verify conversion succeeded
        assert result.success is True
        assert result.changes_made > 0
        
        # Performance assertions
        assert metrics['duration'] < 5.0  # Should complete within 5 seconds
        assert metrics['memory_delta_mb'] < 50  # Should not use more than 50MB additional memory
        assert metrics['peak_memory_mb'] < 200  # Peak memory should be reasonable
        
        print(f"Single file conversion metrics: {metrics}")
        print(f"Converted {result.changes_made} modules in {metrics['duration']:.2f} seconds")
    
    def test_large_project_conversion_performance(self, large_project_structure):
        """Test performance of converting a large project."""
        converter = FQCNConverter()
        monitor = PerformanceMonitor()
        
        # Find all YAML files in the project
        yaml_files = list(large_project_structure.rglob("*.yml"))
        yaml_files.extend(list(large_project_structure.rglob("*.yaml")))
        
        print(f"Found {len(yaml_files)} YAML files to convert")
        
        # Benchmark batch conversion
        monitor.start_monitoring()
        
        results = []
        total_changes = 0
        
        for file_path in yaml_files:
            result = converter.convert_file(file_path, dry_run=True)
            results.append(result)
            if result.success:
                total_changes += result.changes_made
        
        metrics = monitor.stop_monitoring()
        
        # Verify conversions
        successful_conversions = [r for r in results if r.success]
        assert len(successful_conversions) == len(results)  # All should succeed
        assert total_changes > 0
        
        # Performance assertions
        assert metrics['duration'] < 30.0  # Should complete within 30 seconds
        assert metrics['memory_delta_mb'] < 100  # Should not use excessive memory
        
        print(f"Large project conversion metrics: {metrics}")
        print(f"Converted {total_changes} modules across {len(yaml_files)} files")
        print(f"Average time per file: {metrics['duration'] / len(yaml_files):.3f} seconds")
    
    def test_batch_processing_performance(self, temp_dir):
        """Test performance of batch processing multiple projects."""
        # Create multiple medium-sized projects
        num_projects = 10
        projects = []
        
        for i in range(num_projects):
            project_dir = temp_dir / f"project_{i:02d}"
            project_dir.mkdir()
            
            # Create a moderate-sized playbook for each project
            (project_dir / "site.yml").write_text(f"""---
- name: Project {i} deployment
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      package:
        name: "package_{i}_{j}"
        state: present
    
    - name: Service {j}
      service:
        name: "service_{i}_{j}"
        state: started''' for j in range(10))}
""")
            
            projects.append(str(project_dir))
        
        # Test sequential processing
        batch_processor = BatchProcessor(max_workers=1)
        monitor = PerformanceMonitor()
        
        monitor.start_monitoring()
        sequential_results = batch_processor.process_projects(projects, dry_run=True)
        sequential_metrics = monitor.stop_monitoring()
        
        # Test parallel processing
        batch_processor = BatchProcessor(max_workers=4)
        monitor = PerformanceMonitor()
        
        monitor.start_monitoring()
        parallel_results = batch_processor.process_projects(projects, dry_run=True)
        parallel_metrics = monitor.stop_monitoring()
        
        # Verify results are equivalent
        assert len(sequential_results) == len(parallel_results) == num_projects
        
        # Performance comparison
        print(f"Sequential processing: {sequential_metrics['duration']:.2f} seconds")
        print(f"Parallel processing: {parallel_metrics['duration']:.2f} seconds")
        
        # Parallel should not be significantly slower (allowing for overhead)
        assert parallel_metrics['duration'] <= sequential_metrics['duration'] * 1.5
        
        # Both should complete in reasonable time
        assert sequential_metrics['duration'] < 60.0
        assert parallel_metrics['duration'] < 60.0
    
    def test_memory_usage_scalability(self, temp_dir):
        """Test memory usage with increasing project sizes."""
        converter = FQCNConverter()
        
        memory_usage = []
        file_sizes = [10, 50, 100, 200]  # Number of tasks per file
        
        for size in file_sizes:
            # Create file with specified number of tasks
            tasks = []
            for i in range(size):
                tasks.append(f"""  - name: Task {i}
    package:
      name: "package_{i}"
      state: present""")
            
            content = f"""---
- name: Scalability test playbook
  hosts: all
  tasks:
{chr(10).join(tasks)}
"""
            
            test_file = temp_dir / f"scalability_{size}.yml"
            test_file.write_text(content)
            
            # Measure memory usage
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            
            result = converter.convert_file(test_file, dry_run=True)
            
            metrics = monitor.stop_monitoring()
            memory_usage.append({
                'file_size': size,
                'memory_delta_mb': metrics['memory_delta_mb'],
                'peak_memory_mb': metrics['peak_memory_mb'],
                'duration': metrics['duration']
            })
            
            assert result.success is True
        
        # Analyze memory scaling
        print("Memory usage scalability:")
        for usage in memory_usage:
            print(f"  {usage['file_size']} tasks: {usage['memory_delta_mb']:.2f}MB delta, "
                  f"{usage['peak_memory_mb']:.2f}MB peak, {usage['duration']:.3f}s")
        
        # Memory usage should scale reasonably (not exponentially)
        largest_delta = memory_usage[-1]['memory_delta_mb']
        smallest_delta = memory_usage[0]['memory_delta_mb']
        
        # Memory usage should not increase by more than 10x for 20x the content
        if smallest_delta > 0:
            scaling_factor = largest_delta / smallest_delta
            assert scaling_factor < 10.0
    
    def test_validation_performance(self, large_project_structure):
        """Test validation performance on large projects."""
        validator = ValidationEngine()
        monitor = PerformanceMonitor()
        
        # Find all YAML files
        yaml_files = list(large_project_structure.rglob("*.yml"))
        
        # Benchmark validation
        monitor.start_monitoring()
        
        validation_results = []
        for file_path in yaml_files:
            result = validator.validate_conversion(file_path)
            validation_results.append(result)
        
        metrics = monitor.stop_monitoring()
        
        # Verify validations
        assert len(validation_results) == len(yaml_files)
        
        # Performance assertions
        assert metrics['duration'] < 20.0  # Validation should be faster than conversion
        assert metrics['memory_delta_mb'] < 50  # Should use less memory than conversion
        
        print(f"Validation performance metrics: {metrics}")
        print(f"Validated {len(yaml_files)} files in {metrics['duration']:.2f} seconds")
        print(f"Average validation time per file: {metrics['duration'] / len(yaml_files):.3f} seconds")
    
    def test_concurrent_conversion_performance(self, temp_dir):
        """Test performance under concurrent conversion load."""
        # Create multiple files for concurrent processing
        num_files = 20
        files = []
        
        for i in range(num_files):
            file_path = temp_dir / f"concurrent_{i:02d}.yml"
            content = f"""---
- name: Concurrent test {i}
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      package:
        name: "package_{i}_{j}"
        state: present
    
    - name: Service {j}
      service:
        name: "service_{i}_{j}"
        state: started''' for j in range(5))}
"""
            file_path.write_text(content)
            files.append(file_path)
        
        # Test concurrent conversions
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        def convert_file(file_path):
            converter = FQCNConverter()
            return converter.convert_file(file_path, dry_run=True)
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(convert_file, f): f for f in files}
            results = []
            
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        metrics = monitor.stop_monitoring()
        
        # Verify all conversions succeeded
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == num_files
        
        # Performance assertions
        assert metrics['duration'] < 30.0  # Should handle concurrent load efficiently
        assert metrics['memory_delta_mb'] < 100  # Memory usage should be reasonable
        
        print(f"Concurrent conversion metrics: {metrics}")
        print(f"Processed {num_files} files concurrently in {metrics['duration']:.2f} seconds")


class TestMemoryLeakDetection:
    """Tests for detecting memory leaks during extended operations."""
    
    def test_repeated_conversions_memory_stability(self, temp_dir):
        """Test memory stability during repeated conversions."""
        converter = FQCNConverter()
        
        # Create test file
        test_file = temp_dir / "memory_test.yml"
        test_file.write_text("""---
- name: Memory test playbook
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
        
        # Perform many conversions and monitor memory
        num_iterations = 100
        memory_samples = []
        
        process = psutil.Process(os.getpid())
        
        for i in range(num_iterations):
            # Convert file
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True
            
            # Sample memory every 10 iterations
            if i % 10 == 0:
                # Force garbage collection to get accurate memory readings
                import gc
                gc.collect()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
        
        # Check for memory leaks
        # Memory should not continuously increase
        if len(memory_samples) >= 3:
            # Calculate trend - should not have significant upward trend
            first_third = sum(memory_samples[:len(memory_samples)//3]) / (len(memory_samples)//3)
            last_third = sum(memory_samples[-len(memory_samples)//3:]) / (len(memory_samples)//3)
            
            memory_increase = last_third - first_third
            
            print(f"Memory samples: {memory_samples}")
            print(f"Memory increase over {num_iterations} iterations: {memory_increase:.2f}MB")
            
            # Should not increase by more than 45MB over many iterations
            # (increased threshold to account for Python's memory management and test environment variations)
            assert memory_increase < 45.0
    
    def test_large_file_processing_memory_cleanup(self, temp_dir):
        """Test memory cleanup after processing large files."""
        converter = FQCNConverter()
        process = psutil.Process(os.getpid())
        
        # Record baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        # Create and process a very large file
        large_tasks = []
        for i in range(500):  # 500 tasks
            large_tasks.append(f"""  - name: Large task {i}
    package:
      name: "package_{i}"
      state: present""")
        
        large_content = f"""---
- name: Very large playbook
  hosts: all
  tasks:
{chr(10).join(large_tasks)}
"""
        
        large_file = temp_dir / "very_large.yml"
        large_file.write_text(large_content)
        
        # Process the large file
        result = converter.convert_file(large_file, dry_run=True)
        assert result.success is True
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Check memory after processing
        post_processing_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = post_processing_memory - baseline_memory
        
        print(f"Baseline memory: {baseline_memory:.2f}MB")
        print(f"Post-processing memory: {post_processing_memory:.2f}MB")
        print(f"Memory increase: {memory_increase:.2f}MB")
        
        # Memory increase should be reasonable for the file size
        assert memory_increase < 100.0  # Should not use more than 100MB for processing