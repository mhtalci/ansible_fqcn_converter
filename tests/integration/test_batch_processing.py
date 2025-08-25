"""
Batch processing integration tests for FQCN Converter.

These tests validate batch processing functionality with parallel execution,
project discovery, and comprehensive reporting.
"""

import pytest
import tempfile
import time
import concurrent.futures
from pathlib import Path
from unittest.mock import patch

from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.core.converter import FQCNConverter


class TestBatchProcessing:
    """Integration tests for batch processing functionality."""
    
    @pytest.fixture
    def multiple_projects(self, temp_dir):
        """Create multiple Ansible projects for batch testing."""
        projects = {}
        
        # Project 1: Simple web server
        project1 = temp_dir / "project1"
        project1.mkdir()
        
        (project1 / "site.yml").write_text("""---
- name: Web server setup
  hosts: webservers
  tasks:
    - name: Install nginx
      package:
        name: nginx
        state: present
    
    - name: Start nginx
      service:
        name: nginx
        state: started
""")
        
        (project1 / "inventory.ini").write_text("""[webservers]
web1.example.com
""")
        
        projects['project1'] = project1
        
        # Project 2: Database server with roles
        project2 = temp_dir / "project2"
        (project2 / "roles" / "database" / "tasks").mkdir(parents=True)
        
        (project2 / "database.yml").write_text("""---
- name: Database setup
  hosts: databases
  roles:
    - database
""")
        
        (project2 / "roles" / "database" / "tasks" / "main.yml").write_text("""---
- name: Install MySQL
  package:
    name: mysql-server
    state: present

- name: Create database user
  user:
    name: dbuser
    state: present
    system: yes

- name: Start MySQL service
  service:
    name: mysql
    state: started
    enabled: yes

- name: Copy database config
  copy:
    src: my.cnf
    dest: /etc/mysql/my.cnf
    owner: root
    group: root
    mode: '0644'
""")
        
        projects['project2'] = project2
        
        # Project 3: Complex multi-role project
        project3 = temp_dir / "project3"
        (project3 / "roles" / "common" / "tasks").mkdir(parents=True)
        (project3 / "roles" / "webserver" / "tasks").mkdir(parents=True)
        (project3 / "roles" / "webserver" / "handlers").mkdir(parents=True)
        
        (project3 / "site.yml").write_text("""---
- name: Common setup
  hosts: all
  roles:
    - common

- name: Web servers
  hosts: webservers
  roles:
    - webserver
""")
        
        (project3 / "roles" / "common" / "tasks" / "main.yml").write_text("""---
- name: Update package cache
  package:
    update_cache: yes

- name: Install common packages
  package:
    name: "{{ item }}"
    state: present
  loop:
    - curl
    - wget
    - vim

- name: Create common user
  user:
    name: appuser
    state: present
    shell: /bin/bash
""")
        
        (project3 / "roles" / "webserver" / "tasks" / "main.yml").write_text("""---
- name: Install Apache
  package:
    name: apache2
    state: present

- name: Configure Apache
  template:
    src: apache.conf.j2
    dest: /etc/apache2/apache2.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart apache

- name: Start Apache
  service:
    name: apache2
    state: started
    enabled: yes
""")
        
        (project3 / "roles" / "webserver" / "handlers" / "main.yml").write_text("""---
- name: restart apache
  service:
    name: apache2
    state: restarted
""")
        
        projects['project3'] = project3
        
        # Project 4: Invalid project (for error testing)
        project4 = temp_dir / "project4"
        project4.mkdir()
        
        (project4 / "broken.yml").write_text("""---
- name: Broken playbook
  hosts: all
  tasks:
    - name: Invalid YAML
      invalid: [
""")
        
        projects['project4'] = project4
        
        # Non-Ansible directory (should be ignored)
        non_ansible = temp_dir / "not_ansible"
        non_ansible.mkdir()
        (non_ansible / "readme.txt").write_text("This is not an Ansible project")
        
        return projects
    
    def test_project_discovery(self, multiple_projects, temp_dir):
        """Test automatic project discovery."""
        batch_processor = BatchProcessor()
        
        discovered_projects = batch_processor.discover_projects(str(temp_dir))
        
        # Should find 4 Ansible projects (including the broken one)
        assert len(discovered_projects) == 4
        
        project_names = [Path(p).name for p in discovered_projects]
        assert 'project1' in project_names
        assert 'project2' in project_names
        assert 'project3' in project_names
        assert 'project4' in project_names
        assert 'not_ansible' not in project_names
    
    def test_batch_conversion_sequential(self, multiple_projects, temp_dir):
        """Test batch conversion in sequential mode."""
        batch_processor = BatchProcessor(max_workers=1)
        
        # Get valid projects (exclude broken one for this test)
        valid_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project2']),
            str(multiple_projects['project3'])
        ]
        
        # Perform batch conversion
        results = batch_processor.process_projects(valid_projects, dry_run=True)
        
        assert len(results) == 3
        
        # All should succeed in dry run
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == 3
        
        # Check that modules were identified for conversion
        total_modules = sum(r['modules_converted'] for r in results)
        assert total_modules > 0
    
    def test_batch_conversion_parallel(self, multiple_projects, temp_dir):
        """Test batch conversion with parallel processing."""
        batch_processor = BatchProcessor(max_workers=3)
        
        valid_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project2']),
            str(multiple_projects['project3'])
        ]
        
        # Measure execution time
        start_time = time.time()
        results = batch_processor.process_projects(valid_projects, dry_run=True)
        parallel_time = time.time() - start_time
        
        assert len(results) == 3
        
        # All should succeed
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == 3
        
        # Compare with sequential processing
        batch_processor_sequential = BatchProcessor(max_workers=1)
        start_time = time.time()
        sequential_results = batch_processor_sequential.process_projects(valid_projects, dry_run=True)
        sequential_time = time.time() - start_time
        
        # Results should be equivalent
        assert len(sequential_results) == len(results)
        
        # Parallel should not be significantly slower (allowing for overhead)
        # In practice, parallel might be faster for I/O bound operations
        assert parallel_time <= sequential_time * 2  # Allow some overhead
    
    def test_batch_conversion_actual(self, multiple_projects, temp_dir):
        """Test actual batch conversion (not dry run)."""
        batch_processor = BatchProcessor(max_workers=2)
        
        # Use only valid projects
        valid_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project2'])
        ]
        
        # Perform actual conversion
        results = batch_processor.process_projects(valid_projects, dry_run=False)
        
        assert len(results) == 2
        
        # All should succeed
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == 2
        
        # Verify files were actually converted
        project1_site = multiple_projects['project1'] / "site.yml"
        project1_content = project1_site.read_text()
        assert 'ansible.builtin.package:' in project1_content
        assert 'ansible.builtin.service:' in project1_content
        
        project2_tasks = multiple_projects['project2'] / "roles" / "database" / "tasks" / "main.yml"
        project2_content = project2_tasks.read_text()
        assert 'ansible.builtin.package:' in project2_content
        assert 'ansible.builtin.user:' in project2_content
        assert 'ansible.builtin.service:' in project2_content
        assert 'ansible.builtin.copy:' in project2_content
    
    def test_batch_error_handling(self, multiple_projects, temp_dir):
        """Test batch processing error handling."""
        batch_processor = BatchProcessor(max_workers=2)
        
        # Include the broken project
        all_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project4']),  # Broken project
            str(multiple_projects['project2'])
        ]
        
        results = batch_processor.process_projects(all_projects, dry_run=True)
        
        assert len(results) == 3
        
        # Should have some successes and some failures
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        assert len(successful_results) >= 2  # project1 and project2 should succeed
        assert len(failed_results) >= 1     # project4 should fail
        
        # Check that failures have error messages
        for failed_result in failed_results:
            assert failed_result['error_message'] is not None
            assert len(failed_result['error_message']) > 0
    
    def test_batch_reporting(self, multiple_projects, temp_dir):
        """Test batch processing report generation."""
        batch_processor = BatchProcessor(max_workers=2)
        
        valid_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project2']),
            str(multiple_projects['project3'])
        ]
        
        # Process projects
        results = batch_processor.process_projects(valid_projects, dry_run=True)
        
        # Generate report
        report_file = temp_dir / "batch_report.json"
        report = batch_processor.generate_report(str(report_file))
        
        # Verify report structure
        assert 'batch_conversion_report' in report
        batch_report = report['batch_conversion_report']
        
        assert 'summary' in batch_report
        assert 'project_results' in batch_report
        
        # Check summary
        summary = batch_report['summary']
        assert summary['total_projects'] == 3
        assert summary['successful_projects'] >= 2
        assert summary['failed_projects'] >= 0
        
        # Check that report file was created
        assert report_file.exists()
        
        # Verify report contains project details
        project_results = batch_report['project_results']
        assert len(project_results) == 3
        
        for project_result in project_results:
            assert 'project_path' in project_result
            assert 'success' in project_result
            assert 'files_processed' in project_result
            assert 'modules_converted' in project_result

    def test_custom_project_patterns(self, temp_dir):
        """Test batch processing with custom project discovery patterns."""
        # Create projects with non-standard file names
        custom_project1 = temp_dir / "custom1"
        custom_project1.mkdir()
        
        (custom_project1 / "deploy.yml").write_text("""---
- name: Custom deployment
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        custom_project2 = temp_dir / "custom2"
        custom_project2.mkdir()
        
        (custom_project2 / "provision.yaml").write_text("""---
- name: Custom provisioning
  hosts: all
  tasks:
    - name: Create user
      user:
        name: testuser
        state: present
""")
        
        batch_processor = BatchProcessor()
        
        # Should not find projects with default patterns
        default_projects = batch_processor.discover_projects(str(temp_dir))
        assert len(default_projects) == 0
        
        # Should find projects with custom patterns
        custom_projects = batch_processor.discover_projects(
            str(temp_dir), 
            patterns=['deploy.yml', 'provision.yaml']
        )
        assert len(custom_projects) == 2
    
    def test_batch_performance_monitoring(self, multiple_projects, temp_dir):
        """Test performance monitoring during batch processing."""
        batch_processor = BatchProcessor(max_workers=2)
        
        valid_projects = [
            str(multiple_projects['project1']),
            str(multiple_projects['project2']),
            str(multiple_projects['project3'])
        ]
        
        # Process with timing
        start_time = time.time()
        results = batch_processor.process_projects(valid_projects, dry_run=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Verify timing information is reasonable
        assert total_time > 0
        assert total_time < 30  # Should complete within 30 seconds
        
        # Check that each result has timing information
        for result in results:
            if 'processing_time' in result:
                assert result['processing_time'] >= 0
    
    def test_batch_with_large_projects(self, temp_dir):
        """Test batch processing with larger, more complex projects."""
        # Create a larger project with many files
        large_project = temp_dir / "large_project"
        
        # Create multiple roles
        roles = ['webserver', 'database', 'loadbalancer', 'monitoring', 'backup']
        
        for role in roles:
            role_dir = large_project / "roles" / role
            (role_dir / "tasks").mkdir(parents=True)
            (role_dir / "handlers").mkdir(parents=True)
            (role_dir / "vars").mkdir(parents=True)
            
            # Create tasks file for each role
            (role_dir / "tasks" / "main.yml").write_text(f"""---
- name: Install {role} packages
  package:
    name: "{{{{ {role}_packages }}}}"
    state: present

- name: Configure {role}
  template:
    src: {role}.conf.j2
    dest: /etc/{role}/{role}.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart {role}

- name: Start {role} service
  service:
    name: {role}
    state: started
    enabled: yes

- name: Create {role} user
  user:
    name: {role}
    system: yes
    shell: /bin/false
""")
            
            # Create handlers
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
        
        # Create main playbooks
        roles_yaml = '\n'.join(f'    - {role}' for role in roles)
        (large_project / "site.yml").write_text(f"""---
- name: Configure all servers
  hosts: all
  roles:
{roles_yaml}
""")
        
        # Create group-specific playbooks
        for role in roles:
            (large_project / f"{role}s.yml").write_text(f"""---
- name: Configure {role} servers
  hosts: {role}s
  roles:
    - {role}
""")
        
        batch_processor = BatchProcessor(max_workers=3)
        
        # Process the large project
        start_time = time.time()
        results = batch_processor.process_projects([str(large_project)], dry_run=True)
        processing_time = time.time() - start_time
        
        assert len(results) == 1
        assert results[0]['success'] is True
        
        # Should have processed many files
        assert results[0]['files_processed'] >= len(roles) * 2 + len(roles) + 1  # tasks + handlers + playbooks
        
        # Should have converted many modules
        assert results[0]['modules_converted'] >= len(roles) * 4  # At least 4 modules per role
        
        # Performance should be reasonable even for large projects
        assert processing_time < 60  # Should complete within 1 minute


class TestBatchProcessorClass:
    """Test the BatchProcessor class directly."""
    
    def test_batch_processor_initialization(self):
        """Test BatchProcessor initialization with different worker counts."""
        # Default initialization
        processor = BatchProcessor()
        assert processor.max_workers >= 1
        
        # Custom worker count
        processor = BatchProcessor(max_workers=8)
        assert processor.max_workers == 8
        
        # Minimum worker count
        processor = BatchProcessor(max_workers=0)
        assert processor.max_workers >= 1  # Should enforce minimum
    
    def test_project_discovery_edge_cases(self, temp_dir):
        """Test project discovery edge cases."""
        processor = BatchProcessor()
        
        # Empty directory
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        projects = processor.discover_projects(str(empty_dir))
        assert len(projects) == 0
        
        # Non-existent directory
        projects = processor.discover_projects(str(temp_dir / "non_existent"))
        assert len(projects) == 0
        
        # Directory with only non-Ansible files
        non_ansible_dir = temp_dir / "non_ansible"
        non_ansible_dir.mkdir()
        (non_ansible_dir / "readme.txt").write_text("Not Ansible")
        (non_ansible_dir / "config.json").write_text('{"key": "value"}')
        
        projects = processor.discover_projects(str(non_ansible_dir))
        assert len(projects) == 0
    
    def test_single_project_conversion(self, temp_dir):
        """Test converting a single project."""
        processor = BatchProcessor()
        
        # Create simple project
        project_dir = temp_dir / "simple_project"
        project_dir.mkdir()
        
        (project_dir / "playbook.yml").write_text("""---
- name: Simple playbook
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
""")
        
        # Convert single project
        result = processor.convert_project(str(project_dir), dry_run=True)
        
        assert result['success'] is True
        assert result['project'] == str(project_dir)
        assert result['files_processed'] >= 1
        assert result['modules_converted'] >= 1
        assert result['error_message'] is None
    
    def test_project_conversion_error_handling(self, temp_dir):
        """Test error handling in single project conversion."""
        processor = BatchProcessor()
        
        # Non-existent project
        result = processor.convert_project("/non/existent/project", dry_run=True)
        
        assert result['success'] is False
        assert result['error_message'] is not None
        assert result['files_processed'] == 0
        assert result['modules_converted'] == 0