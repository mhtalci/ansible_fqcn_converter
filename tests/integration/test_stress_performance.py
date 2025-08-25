"""
Stress testing and performance regression tests for FQCN Converter.

These tests validate system behavior under extreme loads, memory constraints,
and concurrent operations to ensure production readiness.
"""

import pytest
import time
import psutil
import os
import threading
import multiprocessing
import tempfile
import gc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from unittest.mock import patch

from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.core.validator import ValidationEngine


class StressTestGenerator:
    """Generator for stress testing scenarios."""
    
    @staticmethod
    def create_massive_playbook(base_dir: Path, num_tasks: int = 1000) -> Path:
        """Create a playbook with massive number of tasks."""
        playbook_file = base_dir / f"massive_playbook_{num_tasks}.yml"
        
        tasks = []
        modules = ['package', 'service', 'copy', 'template', 'file', 'user', 'group', 
                  'command', 'shell', 'debug', 'set_fact', 'lineinfile', 'cron']
        
        for i in range(num_tasks):
            module = modules[i % len(modules)]
            task = f"""  - name: Massive task {i + 1} - {module}
    {module}:
      name: "item_{i}"
      state: present"""
            tasks.append(task)
        
        content = f"""---
- name: Massive stress test playbook
  hosts: all
  become: yes
  
  vars:
    stress_test_items: {list(range(num_tasks))}
  
  tasks:
{chr(10).join(tasks)}
"""
        
        playbook_file.write_text(content)
        return playbook_file
    
    @staticmethod
    def create_deeply_nested_project(base_dir: Path, depth: int = 10, width: int = 5) -> Path:
        """Create deeply nested project structure."""
        project_dir = base_dir / f"nested_project_d{depth}_w{width}"
        
        def create_nested_roles(current_dir: Path, current_depth: int):
            if current_depth <= 0:
                return
            
            for i in range(width):
                role_dir = current_dir / f"role_l{depth - current_depth}_n{i}"
                (role_dir / "tasks").mkdir(parents=True, exist_ok=True)
                (role_dir / "handlers").mkdir(parents=True, exist_ok=True)
                
                # Create tasks file
                (role_dir / "tasks" / "main.yml").write_text(f"""---
- name: Install packages for role level {depth - current_depth} node {i}
  package:
    name: "{{{{ item }}}}"
    state: present
  loop:
    - "package_l{depth - current_depth}_n{i}_1"
    - "package_l{depth - current_depth}_n{i}_2"

- name: Configure services for role level {depth - current_depth} node {i}
  service:
    name: "service_l{depth - current_depth}_n{i}"
    state: started
    enabled: yes

- name: Create files for role level {depth - current_depth} node {i}
  file:
    path: "/tmp/file_l{depth - current_depth}_n{i}.txt"
    state: touch
    owner: root
    group: root
    mode: '0644'

- name: Include nested roles
  include_role:
    name: "{{{{ item }}}}"
  loop:
{chr(10).join(f'    - "role_l{depth - current_depth + 1}_n{j}"' for j in range(width)) if current_depth > 1 else '    []'}
  when: nested_roles is defined
""")
                
                # Create handlers
                (role_dir / "handlers" / "main.yml").write_text(f"""---
- name: restart service level {depth - current_depth} node {i}
  service:
    name: "service_l{depth - current_depth}_n{i}"
    state: restarted
""")
                
                # Recurse to next level
                create_nested_roles(current_dir, current_depth - 1)
        
        create_nested_roles(project_dir / "roles", depth)
        
        # Create main playbook
        (project_dir / "site.yml").write_text(f"""---
- name: Deeply nested project deployment
  hosts: all
  become: yes
  
  roles:
{chr(10).join(f'    - role_l0_n{i}' for i in range(width))}
""")
        
        return project_dir
    
    @staticmethod
    def create_wide_project_structure(base_dir: Path, num_roles: int = 100) -> Path:
        """Create project with very wide structure (many roles)."""
        project_dir = base_dir / f"wide_project_{num_roles}_roles"
        
        for i in range(num_roles):
            role_dir = project_dir / "roles" / f"role_{i:03d}"
            (role_dir / "tasks").mkdir(parents=True)
            (role_dir / "handlers").mkdir(parents=True)
            (role_dir / "vars").mkdir(parents=True)
            
            # Create tasks for each role
            (role_dir / "tasks" / "main.yml").write_text(f"""---
- name: Install role {i} packages
  package:
    name: "{{{{ item }}}}"
    state: present
  loop:
    - "package_role_{i}_1"
    - "package_role_{i}_2"
    - "package_role_{i}_3"

- name: Configure role {i} service
  service:
    name: "service_role_{i}"
    state: started
    enabled: yes

- name: Create role {i} user
  user:
    name: "user_role_{i}"
    system: yes
    shell: /bin/false

- name: Setup role {i} directories
  file:
    path: "{{{{ item }}}}"
    state: directory
    owner: "user_role_{i}"
    group: "user_role_{i}"
    mode: '0755'
  loop:
    - "/opt/role_{i}"
    - "/var/log/role_{i}"
    - "/etc/role_{i}"

- name: Template role {i} configuration
  template:
    src: "role_{i}.conf.j2"
    dest: "/etc/role_{i}/config.conf"
    owner: "user_role_{i}"
    group: "user_role_{i}"
    mode: '0644'
  notify: restart role {i} service
""")
            
            # Create handlers
            (role_dir / "handlers" / "main.yml").write_text(f"""---
- name: restart role {i} service
  service:
    name: "service_role_{i}"
    state: restarted

- name: reload role {i} service
  service:
    name: "service_role_{i}"
    state: reloaded
""")
        
        # Create main playbook that includes all roles
        roles_list = [f"    - role_{i:03d}" for i in range(num_roles)]
        (project_dir / "site.yml").write_text(f"""---
- name: Wide project with {num_roles} roles
  hosts: all
  become: yes
  
  roles:
{chr(10).join(roles_list)}
""")
        
        return project_dir


class MemoryLeakDetector:
    """Detector for memory leaks during extended operations."""
    
    def __init__(self, threshold_mb: float = 50.0):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = None
        self.memory_samples = []
        
    def start_monitoring(self):
        """Start memory leak monitoring."""
        gc.collect()  # Force garbage collection
        self.baseline_memory = self.process.memory_info().rss
        self.memory_samples = [self.baseline_memory]
        
    def sample_memory(self):
        """Take a memory sample."""
        current_memory = self.process.memory_info().rss
        self.memory_samples.append(current_memory)
        
    def check_for_leaks(self) -> dict:
        """Check for memory leaks and return analysis."""
        if len(self.memory_samples) < 3:
            return {'leak_detected': False, 'reason': 'Insufficient samples'}
        
        # Calculate trend
        recent_samples = self.memory_samples[-10:]  # Last 10 samples
        early_samples = self.memory_samples[:10]    # First 10 samples
        
        recent_avg = sum(recent_samples) / len(recent_samples)
        early_avg = sum(early_samples) / len(early_samples)
        
        memory_increase_mb = (recent_avg - early_avg) / 1024 / 1024
        
        leak_detected = memory_increase_mb > self.threshold_mb
        
        return {
            'leak_detected': leak_detected,
            'memory_increase_mb': memory_increase_mb,
            'threshold_mb': self.threshold_mb,
            'baseline_mb': self.baseline_memory / 1024 / 1024,
            'current_mb': recent_avg / 1024 / 1024,
            'samples_count': len(self.memory_samples)
        }


class TestStressScenarios:
    """Stress testing scenarios for extreme loads."""
    
    def test_massive_single_file_conversion(self, temp_dir):
        """Test conversion of extremely large single files."""
        # Test with different file sizes
        test_sizes = [500, 1000, 2000]
        
        converter = FQCNConverter()
        
        for size in test_sizes:
            massive_file = StressTestGenerator.create_massive_playbook(temp_dir, size)
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = converter.convert_file(massive_file, dry_run=True)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
            
            # Assertions
            assert result.success is True, f"Failed to convert file with {size} tasks"
            assert result.changes_made > 0, f"No changes made for {size} tasks"
            
            # Performance assertions
            assert duration < 30.0, f"Conversion took too long for {size} tasks: {duration:.2f}s"
            assert memory_delta_mb < 200, f"Excessive memory usage for {size} tasks: {memory_delta_mb:.2f}MB"
            
            print(f"Massive file ({size} tasks): {duration:.2f}s, {memory_delta_mb:.2f}MB, {result.changes_made} changes")
    
    def test_deeply_nested_project_stress(self, temp_dir):
        """Test conversion of deeply nested project structures."""
        nested_project = StressTestGenerator.create_deeply_nested_project(temp_dir, depth=8, width=3)
        
        converter = FQCNConverter()
        
        # Find all YAML files
        yaml_files = list(nested_project.rglob("*.yml"))
        yaml_files.extend(list(nested_project.rglob("*.yaml")))
        
        start_time = time.time()
        
        results = []
        for file_path in yaml_files:
            result = converter.convert_file(file_path, dry_run=True)
            results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify results
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(results), "Some conversions failed in nested project"
        
        total_changes = sum(r.changes_made for r in results)
        assert total_changes > 0, "No changes made in nested project"
        
        # Performance assertion
        assert duration < 60.0, f"Nested project conversion took too long: {duration:.2f}s"
        
        print(f"Nested project: {len(yaml_files)} files, {duration:.2f}s, {total_changes} changes")
    
    def test_wide_project_structure_stress(self, temp_dir):
        """Test conversion of very wide project structures."""
        wide_project = StressTestGenerator.create_wide_project_structure(temp_dir, num_roles=50)
        
        converter = FQCNConverter()
        
        # Find all YAML files
        yaml_files = list(wide_project.rglob("*.yml"))
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        results = []
        for file_path in yaml_files:
            result = converter.convert_file(file_path, dry_run=True)
            results.append(result)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        duration = end_time - start_time
        memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
        
        # Verify results
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(results), "Some conversions failed in wide project"
        
        total_changes = sum(r.changes_made for r in results)
        assert total_changes > 0, "No changes made in wide project"
        
        # Performance assertions
        assert duration < 120.0, f"Wide project conversion took too long: {duration:.2f}s"
        assert memory_delta_mb < 300, f"Excessive memory usage: {memory_delta_mb:.2f}MB"
        
        print(f"Wide project: {len(yaml_files)} files, {duration:.2f}s, {memory_delta_mb:.2f}MB, {total_changes} changes")
    
    def test_concurrent_conversion_stress(self, temp_dir):
        """Test system behavior under high concurrent load."""
        # Create multiple projects for concurrent processing
        num_projects = 20
        projects = []
        
        for i in range(num_projects):
            project_dir = temp_dir / f"concurrent_project_{i:02d}"
            project_dir.mkdir()
            
            # Create moderate-sized playbook
            (project_dir / "site.yml").write_text(f"""---
- name: Concurrent project {i}
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      package:
        name: "package_{i}_{j}"
        state: present
    
    - name: Service {j}
      service:
        name: "service_{i}_{j}"
        state: started''' for j in range(25))}
""")
            projects.append(project_dir / "site.yml")
        
        # Test with different concurrency levels
        concurrency_levels = [1, 4, 8, 16]
        
        for max_workers in concurrency_levels:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            def convert_file(file_path):
                converter = FQCNConverter()
                return converter.convert_file(file_path, dry_run=True)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(convert_file, f): f for f in projects}
                results = []
                
                for future in as_completed(future_to_file):
                    result = future.result()
                    results.append(result)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
            
            # Verify all conversions succeeded
            successful_results = [r for r in results if r.success]
            assert len(successful_results) == num_projects, f"Failed conversions with {max_workers} workers"
            
            print(f"Concurrent ({max_workers} workers): {duration:.2f}s, {memory_delta_mb:.2f}MB")
    
    def test_memory_leak_detection(self, temp_dir):
        """Test for memory leaks during extended operations."""
        leak_detector = MemoryLeakDetector(threshold_mb=30.0)
        leak_detector.start_monitoring()
        
        converter = FQCNConverter()
        
        # Perform many conversion operations
        num_iterations = 200
        
        for i in range(num_iterations):
            # Create a test file
            test_file = temp_dir / f"leak_test_{i % 10}.yml"  # Reuse filenames
            test_file.write_text(f"""---
- name: Memory leak test {i}
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
            
            # Convert file
            result = converter.convert_file(test_file, dry_run=True)
            assert result.success is True
            
            # Sample memory every 20 iterations
            if i % 20 == 0:
                leak_detector.sample_memory()
                gc.collect()  # Force garbage collection
        
        # Check for memory leaks
        leak_analysis = leak_detector.check_for_leaks()
        
        print(f"Memory leak analysis: {leak_analysis}")
        
        assert not leak_analysis['leak_detected'], \
            f"Memory leak detected: {leak_analysis['memory_increase_mb']:.2f}MB increase"
    
    def test_batch_processing_extreme_load(self, temp_dir):
        """Test batch processing under extreme load conditions."""
        # Create many projects
        num_projects = 100
        projects = []
        
        for i in range(num_projects):
            project_dir = temp_dir / f"batch_extreme_{i:03d}"
            project_dir.mkdir()
            
            # Create playbook with moderate complexity
            (project_dir / "playbook.yml").write_text(f"""---
- name: Batch extreme test {i}
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      package:
        name: "pkg_{i}_{j}"
        state: present''' for j in range(15))}
""")
            projects.append(str(project_dir))
        
        # Test with maximum workers
        max_workers = min(multiprocessing.cpu_count() * 2, 16)
        batch_processor = BatchProcessor(max_workers=max_workers)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        results = batch_processor.process_projects(projects, dry_run=True)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        duration = end_time - start_time
        memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
        
        # Verify results
        assert len(results) == num_projects
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / num_projects
        
        assert success_rate >= 0.95, f"Low success rate: {success_rate:.2%}"
        
        total_modules = sum(r['modules_converted'] for r in successful_results)
        
        # Performance assertions
        assert duration < 600.0, f"Batch processing took too long: {duration:.2f}s"
        assert memory_delta_mb < 1000, f"Excessive memory usage: {memory_delta_mb:.2f}MB"
        
        print(f"Batch extreme: {num_projects} projects, {duration:.2f}s, "
              f"{memory_delta_mb:.2f}MB, {total_modules} modules, {success_rate:.2%} success")


class TestPerformanceRegression:
    """Performance regression testing with detailed benchmarking."""
    
    def test_conversion_performance_baseline(self, temp_dir):
        """Establish performance baseline for regression testing."""
        converter = FQCNConverter()
        
        # Standard test cases with expected performance characteristics
        test_cases = [
            {"name": "small", "tasks": 10, "max_time": 0.5, "max_memory": 10},
            {"name": "medium", "tasks": 50, "max_time": 2.0, "max_memory": 25},
            {"name": "large", "tasks": 200, "max_time": 8.0, "max_memory": 50},
            {"name": "xlarge", "tasks": 500, "max_time": 20.0, "max_memory": 100}
        ]
        
        baseline_results = {}
        
        for test_case in test_cases:
            # Create test file
            test_file = StressTestGenerator.create_massive_playbook(
                temp_dir, test_case["tasks"]
            )
            
            # Measure performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = converter.convert_file(test_file, dry_run=True)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
            
            baseline_results[test_case["name"]] = {
                'duration': duration,
                'memory_delta_mb': memory_delta_mb,
                'changes_made': result.changes_made,
                'success': result.success
            }
            
            # Regression assertions
            assert result.success is True
            assert duration <= test_case["max_time"], \
                f"Performance regression: {test_case['name']} took {duration:.2f}s (max: {test_case['max_time']}s)"
            assert memory_delta_mb <= test_case["max_memory"], \
                f"Memory regression: {test_case['name']} used {memory_delta_mb:.2f}MB (max: {test_case['max_memory']}MB)"
        
        # Print baseline for future reference
        print("Performance Baseline Results:")
        for name, metrics in baseline_results.items():
            print(f"  {name}: {metrics['duration']:.3f}s, {metrics['memory_delta_mb']:.2f}MB, "
                  f"{metrics['changes_made']} changes")
        
        # Test functions should return None
        assert baseline_results  # Ensure we have results
    
    def test_validation_performance_regression(self, temp_dir):
        """Test validation performance regression."""
        validator = ValidationEngine()
        
        # Create test files of different sizes
        test_sizes = [50, 100, 200, 400]
        validation_results = {}
        
        for size in test_sizes:
            test_file = StressTestGenerator.create_massive_playbook(temp_dir, size)
            
            # First convert the file to have something to validate
            converter = FQCNConverter()
            converter.convert_file(test_file, dry_run=False)
            
            # Measure validation performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = validator.validate_conversion(test_file)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
            
            validation_results[size] = {
                'duration': duration,
                'memory_delta_mb': memory_delta_mb,
                'valid': result.valid
            }
            
            # Validation should be faster than conversion
            assert duration < 5.0, f"Validation too slow for {size} tasks: {duration:.2f}s"
            assert memory_delta_mb < 20, f"Validation memory usage too high: {memory_delta_mb:.2f}MB"
        
        print("Validation Performance Results:")
        for size, metrics in validation_results.items():
            print(f"  {size} tasks: {metrics['duration']:.3f}s, {metrics['memory_delta_mb']:.2f}MB")
    
    def test_batch_processing_scalability(self, temp_dir):
        """Test batch processing scalability characteristics."""
        # Test with increasing numbers of projects
        project_counts = [10, 25, 50, 100]
        scalability_results = {}
        
        for count in project_counts:
            # Create projects
            projects = []
            for i in range(count):
                project_dir = temp_dir / f"scale_test_{count}_{i:03d}"
                project_dir.mkdir()
                
                (project_dir / "site.yml").write_text(f"""---
- name: Scalability test project {i}
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      package:
        name: "pkg_{i}_{j}"
        state: present''' for j in range(10))}
""")
                projects.append(str(project_dir))
            
            # Measure batch processing performance
            batch_processor = BatchProcessor(max_workers=4)
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            results = batch_processor.process_projects(projects, dry_run=True)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_delta_mb = (end_memory - start_memory) / 1024 / 1024
            
            successful_results = [r for r in results if r['success']]
            success_rate = len(successful_results) / len(results)
            
            scalability_results[count] = {
                'duration': duration,
                'memory_delta_mb': memory_delta_mb,
                'success_rate': success_rate,
                'throughput': count / duration  # projects per second
            }
            
            # Scalability assertions
            assert success_rate >= 0.95, f"Low success rate for {count} projects: {success_rate:.2%}"
            assert duration < count * 0.5, f"Poor scalability for {count} projects: {duration:.2f}s"
        
        print("Batch Processing Scalability Results:")
        for count, metrics in scalability_results.items():
            print(f"  {count} projects: {metrics['duration']:.2f}s, "
                  f"{metrics['throughput']:.2f} proj/s, {metrics['success_rate']:.2%} success")
        
        # Check that throughput doesn't degrade significantly
        throughputs = [metrics['throughput'] for metrics in scalability_results.values()]
        min_throughput = min(throughputs)
        max_throughput = max(throughputs)
        
        # Throughput shouldn't degrade by more than 50%
        throughput_ratio = min_throughput / max_throughput
        assert throughput_ratio >= 0.5, f"Significant throughput degradation: {throughput_ratio:.2%}"