"""
API usage examples validation tests for FQCN Converter.

These tests validate that API usage examples in documentation work correctly
and demonstrate proper usage patterns for production environments.
"""

import tempfile
import textwrap
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from fqcn_converter.config.manager import ConfigurationManager
from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.core.converter import ConversionResult, FQCNConverter
from fqcn_converter.core.validator import ValidationEngine, ValidationResult


class TestAPIUsageExamples:
    """Test API usage examples for correctness and completeness."""

    def test_basic_converter_usage_example(self, temp_dir):
        """Test basic converter usage example from documentation."""
        # Example from documentation
        converter = FQCNConverter()

        # Create test file
        test_file = temp_dir / "example.yml"
        test_file.write_text(
            """---
- name: Example playbook
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
"""
        )

        # Convert file (dry run)
        result = converter.convert_file(test_file, dry_run=True)

        # Validate result
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.changes_made > 0
        assert result.file_path == str(test_file)

        # Convert file (actual)
        result = converter.convert_file(test_file, dry_run=False)

        assert result.success is True

        # Verify conversion
        converted_content = test_file.read_text()
        assert "ansible.builtin.package:" in converted_content
        assert "ansible.builtin.service:" in converted_content

    def test_converter_with_custom_config_example(self, temp_dir):
        """Test converter usage with custom configuration."""
        # Create custom configuration
        config_file = temp_dir / "custom_config.yml"
        config_file.write_text(
            """---
ansible_builtin:
  copy: ansible.builtin.copy
  file: ansible.builtin.file
  service: ansible.builtin.service

custom_collection:
  my_module: custom.collection.my_module
"""
        )

        # Initialize converter with custom config
        converter = FQCNConverter(config_path=str(config_file))

        # Create test content
        test_file = temp_dir / "custom_example.yml"
        test_file.write_text(
            """---
- name: Custom config example
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Use custom module
      my_module:
        param: value
"""
        )

        # Convert with custom config
        result = converter.convert_file(test_file, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        converted_content = test_file.read_text()
        assert "ansible.builtin.copy:" in converted_content
        assert "custom.collection.my_module:" in converted_content

    def test_content_conversion_example(self, temp_dir):
        """Test converting content string directly."""
        converter = FQCNConverter()

        # Example content
        content = """---
- name: Content conversion example
  hosts: all
  tasks:
    - name: Create directory
      file:
        path: /opt/app
        state: directory
    
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3
"""

        # Convert content
        result = converter.convert_content(content)

        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.changes_made > 0

        # Verify converted content
        converted = result.converted_content
        assert "ansible.builtin.file:" in converted
        assert "ansible.builtin.package:" in converted

    def test_validation_engine_example(self, temp_dir):
        """Test validation engine usage example."""
        # First convert a file
        converter = FQCNConverter()
        test_file = temp_dir / "validation_example.yml"
        test_file.write_text(
            """---
- name: Validation example
  hosts: all
  tasks:
    - name: Install package
      package:
        name: nginx
        state: present
"""
        )

        converter.convert_file(test_file, dry_run=False)

        # Now validate the converted file
        validator = ValidationEngine()
        result = validator.validate_conversion(test_file)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.file_path == str(test_file)

        # Should have high score after conversion
        if hasattr(result, "score"):
            assert result.score > 0.8

    def test_batch_processing_example(self, temp_dir):
        """Test batch processing usage example."""
        # Create multiple projects
        projects = []

        for i in range(3):
            project_dir = temp_dir / f"project_{i}"
            project_dir.mkdir()

            (project_dir / "site.yml").write_text(
                f"""---
- name: Project {i} playbook
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
"""
            )
            projects.append(str(project_dir))

        # Process projects in batch
        batch_processor = BatchProcessor(max_workers=2)
        results = batch_processor.process_projects(projects, dry_run=True)

        assert len(results) == 3

        # All should succeed
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == 3

        # Should have converted modules
        total_modules = sum(r["modules_converted"] for r in results)
        assert total_modules > 0

    def test_configuration_manager_example(self, temp_dir):
        """Test configuration manager usage example."""
        config_manager = ConfigurationManager()

        # Load default mappings
        default_mappings = config_manager.load_default_mappings()

        assert isinstance(default_mappings, dict)
        assert len(default_mappings) > 0

        # Should have common modules
        assert "package" in default_mappings
        assert "service" in default_mappings
        assert "copy" in default_mappings

        # Create custom mappings
        custom_config = temp_dir / "custom.yml"
        custom_config.write_text(
            """---
custom_modules:
  my_module: custom.collection.my_module
  another_module: another.collection.module
"""
        )

        # Load and merge mappings
        custom_mappings = config_manager.load_custom_mappings(str(custom_config))
        merged_mappings = config_manager.merge_mappings(
            default_mappings, custom_mappings
        )

        assert isinstance(merged_mappings, dict)
        assert len(merged_mappings) >= len(default_mappings)

        # Custom mappings should be included
        if "my_module" in custom_mappings:
            assert "my_module" in merged_mappings

    def test_error_handling_examples(self, temp_dir):
        """Test error handling usage examples."""
        from fqcn_converter.exceptions import (
            ConversionError,
            FileAccessError,
            ValidationError,
        )

        converter = FQCNConverter()

        # Example 1: Handle file not found
        try:
            result = converter.convert_file("/non/existent/file.yml")
        except (ConversionError, FileAccessError, FileNotFoundError, OSError) as e:
            # This is expected behavior
            assert isinstance(
                e, (ConversionError, FileAccessError, FileNotFoundError, OSError)
            )

        # Example 2: Handle invalid YAML
        invalid_file = temp_dir / "invalid.yml"
        invalid_file.write_text("invalid: yaml: content: [")

        try:
            result = converter.convert_file(invalid_file)
        except (ConversionError, Exception) as e:
            # This is expected for invalid YAML
            assert isinstance(e, Exception)

        # Example 3: Graceful handling with validation
        validator = ValidationEngine()

        try:
            result = validator.validate_conversion("/non/existent/file.yml")
        except (ValidationError, FileAccessError, FileNotFoundError, OSError) as e:
            # This is expected behavior
            assert isinstance(
                e, (ValidationError, FileAccessError, FileNotFoundError, OSError)
            )

    def test_advanced_usage_patterns(self, temp_dir):
        """Test advanced usage patterns and workflows."""
        # Pattern 1: Convert and validate workflow
        converter = FQCNConverter()
        validator = ValidationEngine()

        test_file = temp_dir / "workflow_example.yml"
        test_file.write_text(
            """---
- name: Workflow example
  hosts: all
  tasks:
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - php
        - mysql-client
    
    - name: Configure services
      service:
        name: "{{ item }}"
        state: started
        enabled: yes
      loop:
        - nginx
        - php-fpm
"""
        )

        # Step 1: Convert
        conversion_result = converter.convert_file(test_file, dry_run=False)
        assert conversion_result.success is True

        # Step 2: Validate
        validation_result = validator.validate_conversion(test_file)
        assert validation_result.valid is True

        # Pattern 2: Batch processing with validation
        projects = []
        for i in range(2):
            project_dir = temp_dir / f"batch_project_{i}"
            project_dir.mkdir()

            (project_dir / "playbook.yml").write_text(
                f"""---
- name: Batch project {i}
  hosts: all
  tasks:
    - name: Task {i}
      copy:
        src: file_{i}.txt
        dest: /tmp/file_{i}.txt
"""
            )
            projects.append(str(project_dir))

        # Batch convert
        batch_processor = BatchProcessor()
        batch_results = batch_processor.process_projects(projects, dry_run=False)

        # Validate all converted files
        for project_path in projects:
            project_dir = Path(project_path)
            playbook_file = project_dir / "playbook.yml"

            if playbook_file.exists():
                validation_result = validator.validate_conversion(playbook_file)
                assert validation_result.valid is True

    def test_integration_with_external_tools(self, temp_dir):
        """Test integration patterns with external tools."""
        # Pattern: Pre-processing and post-processing
        converter = FQCNConverter()

        # Create a playbook that might come from external tool
        external_generated = temp_dir / "external_generated.yml"
        external_generated.write_text(
            """---
# Generated by external tool
- name: External tool generated playbook
  hosts: "{{ target_hosts | default('all') }}"
  vars:
    packages_to_install:
      - "{{ web_server | default('nginx') }}"
      - "{{ database | default('mysql-server') }}"
  
  tasks:
    - name: Install required packages
      package:
        name: "{{ item }}"
        state: present
      loop: "{{ packages_to_install }}"
    
    - name: Configure firewall
      command: "ufw allow {{ item }}"
      loop:
        - "80/tcp"
        - "443/tcp"
      when: configure_firewall | default(true)
    
    - name: Start services
      service:
        name: "{{ item }}"
        state: started
        enabled: yes
      loop: "{{ packages_to_install }}"
"""
        )

        # Convert the externally generated playbook
        result = converter.convert_file(external_generated, dry_run=False)

        assert result.success is True
        assert result.changes_made > 0

        # Verify conversion preserved variables and logic
        converted_content = external_generated.read_text()
        assert "ansible.builtin.package:" in converted_content
        assert "ansible.builtin.command:" in converted_content
        assert "ansible.builtin.service:" in converted_content

        # Variables and conditionals should be preserved
        assert "{{ target_hosts | default('all') }}" in converted_content
        assert "when: configure_firewall | default(true)" in converted_content

    def test_performance_usage_patterns(self, temp_dir):
        """Test performance-oriented usage patterns."""
        # Pattern: Large file processing
        converter = FQCNConverter()

        # Create a large playbook
        tasks = []
        for i in range(100):
            tasks.append(
                f"""  - name: Task {i}
    package:
      name: "package_{i}"
      state: present
  
  - name: Service {i}
    service:
      name: "service_{i}"
      state: started"""
            )

        large_playbook = temp_dir / "large_playbook.yml"
        large_playbook.write_text(
            f"""---
- name: Large playbook performance test
  hosts: all
  tasks:
{chr(10).join(tasks)}
"""
        )

        # Measure conversion performance
        import time

        start_time = time.time()

        result = converter.convert_file(large_playbook, dry_run=True)

        end_time = time.time()
        duration = end_time - start_time

        assert result.success is True
        assert result.changes_made > 0

        # Should complete in reasonable time
        assert duration < 10.0, f"Large file conversion took too long: {duration:.2f}s"

        # Pattern: Memory-efficient batch processing
        batch_processor = BatchProcessor(max_workers=2)

        # Create multiple moderate-sized projects
        projects = []
        for i in range(10):
            project_dir = temp_dir / f"perf_project_{i}"
            project_dir.mkdir()

            (project_dir / "site.yml").write_text(
                f"""---
- name: Performance project {i}
  hosts: all
  tasks:
{chr(10).join(f'''    - name: Task {j}
      copy:
        src: "file_{i}_{j}.txt"
        dest: "/tmp/file_{i}_{j}.txt"''' for j in range(10))}
"""
            )
            projects.append(str(project_dir))

        # Process in batch
        start_time = time.time()
        results = batch_processor.process_projects(projects, dry_run=True)
        end_time = time.time()

        batch_duration = end_time - start_time

        assert len(results) == 10
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == 10

        # Batch processing should be efficient
        assert (
            batch_duration < 30.0
        ), f"Batch processing took too long: {batch_duration:.2f}s"


class TestAPIDocumentationExamples:
    """Test that examples in API documentation are accurate and working."""

    def test_readme_examples(self, temp_dir):
        """Test examples that would appear in README documentation."""
        # Basic usage example
        converter = FQCNConverter()

        # Create example playbook
        playbook = temp_dir / "example.yml"
        playbook.write_text(
            textwrap.dedent(
                """
        ---
        - name: Web server setup
          hosts: webservers
          become: yes
          
          tasks:
            - name: Install web server
              package:
                name: nginx
                state: present
            
            - name: Start web server
              service:
                name: nginx
                state: started
                enabled: yes
            
            - name: Copy configuration
              copy:
                src: nginx.conf
                dest: /etc/nginx/nginx.conf
                backup: yes
              notify: restart nginx
          
          handlers:
            - name: restart nginx
              service:
                name: nginx
                state: restarted
        """
            ).strip()
        )

        # Convert the playbook
        result = converter.convert_file(playbook)

        assert result.success
        assert result.changes_made > 0

        # Verify the conversion
        content = playbook.read_text()
        assert "ansible.builtin.package:" in content
        assert "ansible.builtin.service:" in content
        assert "ansible.builtin.copy:" in content

    def test_cli_equivalent_examples(self, temp_dir):
        """Test programmatic equivalents of CLI usage."""
        # Equivalent of: fqcn-converter convert playbook.yml
        converter = FQCNConverter()

        playbook = temp_dir / "cli_example.yml"
        playbook.write_text(
            """---
- hosts: all
  tasks:
    - package: name=vim state=present
    - service: name=sshd state=restarted
"""
        )

        result = converter.convert_file(playbook, dry_run=False)
        assert result.success

        # Equivalent of: fqcn-converter validate playbook.yml
        validator = ValidationEngine()
        validation_result = validator.validate_conversion(playbook)
        assert validation_result.valid

        # Equivalent of: fqcn-converter batch /path/to/projects
        batch_processor = BatchProcessor()

        # Create a project directory
        project_dir = temp_dir / "batch_example"
        project_dir.mkdir()
        (project_dir / "site.yml").write_text(
            """---
- hosts: all
  tasks:
    - copy: src=file.txt dest=/tmp/file.txt
"""
        )

        batch_results = batch_processor.process_projects(
            [str(project_dir)], dry_run=True
        )
        assert len(batch_results) == 1
        assert batch_results[0]["success"]

    def test_cookbook_examples(self, temp_dir):
        """Test cookbook-style examples for common scenarios."""
        converter = FQCNConverter()

        # Scenario 1: Converting legacy Ansible 2.9 playbooks
        legacy_playbook = temp_dir / "legacy.yml"
        legacy_playbook.write_text(
            """---
- hosts: webservers
  sudo: yes
  
  tasks:
    - name: install apache
      yum: name=httpd state=present
    
    - name: start apache
      service: name=httpd state=started enabled=yes
    
    - name: copy config
      copy: src=httpd.conf dest=/etc/httpd/conf/httpd.conf
"""
        )

        result = converter.convert_file(legacy_playbook, dry_run=False)
        assert result.success

        content = legacy_playbook.read_text()
        assert "ansible.builtin.yum:" in content
        assert "ansible.builtin.service:" in content
        assert "ansible.builtin.copy:" in content

        # Scenario 2: Handling mixed FQCN and short names
        mixed_playbook = temp_dir / "mixed.yml"
        mixed_playbook.write_text(
            """---
- name: Mixed FQCN example
  hosts: all
  
  tasks:
    # Already FQCN - should not change
    - name: Docker container
      community.docker.docker_container:
        name: web
        image: nginx
        state: started
    
    # Short names - should be converted
    - name: Install package
      package:
        name: docker.io
        state: present
    
    - name: Start service
      service:
        name: docker
        state: started
"""
        )

        result = converter.convert_file(mixed_playbook, dry_run=False)
        assert result.success

        content = mixed_playbook.read_text()
        # FQCN should remain unchanged
        assert "community.docker.docker_container:" in content
        # Short names should be converted
        assert "ansible.builtin.package:" in content
        assert "ansible.builtin.service:" in content

    def test_troubleshooting_examples(self, temp_dir):
        """Test examples for troubleshooting common issues."""
        converter = FQCNConverter()

        # Example: Handling files with syntax errors
        problematic_file = temp_dir / "problematic.yml"
        problematic_file.write_text(
            """---
- name: File with issues
  hosts: all
  tasks:
    - name: Valid task
      package:
        name: nginx
        state: present
    
    # This task has a potential issue but should still be convertible
    - name: Task with complex variables
      template:
        src: "{{ item.src }}"
        dest: "{{ item.dest }}"
      loop:
        - { src: "template1.j2", dest: "/etc/config1.conf" }
        - { src: "template2.j2", dest: "/etc/config2.conf" }
"""
        )

        # Should handle complex variable structures
        result = converter.convert_file(problematic_file, dry_run=False)
        assert result.success

        content = problematic_file.read_text()
        assert "ansible.builtin.package:" in content
        assert "ansible.builtin.template:" in content

        # Variables should be preserved
        assert "{{ item.src }}" in content
        assert "{{ item.dest }}" in content
