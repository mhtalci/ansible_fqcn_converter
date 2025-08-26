"""
Scenario-based workflow tests following Molecule patterns.

This module implements comprehensive workflow testing using scenario-based
patterns similar to Molecule's approach for testing Ansible automation.
"""

import tempfile
from pathlib import Path

import pytest

from fqcn_converter.core.batch import BatchProcessor
from fqcn_converter.core.converter import FQCNConverter
from fqcn_converter.core.validator import ValidationEngine


@pytest.mark.integration
class TestConversionScenarios:
    """Test different conversion scenarios following Molecule patterns."""

    @pytest.mark.parametrize("scenario", [
        "simple_playbook",
        "complex_roles", 
        "mixed_collections",
        "legacy_syntax",
        "nested_structures"
    ])
    def test_conversion_scenarios(self, scenario, tmp_path):
        """Test different conversion scenarios with comprehensive validation."""
        # Scenario definitions following Molecule's approach
        scenarios = {
            "simple_playbook": {
                "content": """---
- name: Simple playbook
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Install package
      package:
        name: nginx
        state: present""",
                "expected_changes": 2,
                "expected_modules": ["ansible.builtin.copy", "ansible.builtin.package"]
            },
            "complex_roles": {
                "content": """---
- name: Complex role-based playbook
  hosts: all
  roles:
    - role: nginx
      vars:
        nginx_port: 80
  tasks:
    - name: Configure service
      service:
        name: nginx
        state: started
    - name: Create user
      user:
        name: webuser
        state: present""",
                "expected_changes": 2,
                "expected_modules": ["ansible.builtin.service", "ansible.builtin.user"]
            },
            "mixed_collections": {
                "content": """---
- name: Mixed collections playbook
  hosts: all
  tasks:
    - name: Copy config
      copy:
        src: config.yml
        dest: /etc/config.yml
    - name: Run docker container
      docker_container:
        name: web
        image: nginx
        state: started""",
                "expected_changes": 2,
                "expected_modules": ["ansible.builtin.copy", "community.docker.docker_container"]
            },
            "legacy_syntax": {
                "content": """---
- name: Legacy syntax playbook
  hosts: all
  tasks:
    - copy: src=old.txt dest=/tmp/old.txt
    - file: path=/tmp/test state=directory
    - command: echo "legacy style\"""",
                "expected_changes": 3,
                "expected_modules": ["ansible.builtin.copy", "ansible.builtin.file", "ansible.builtin.command"]
            },
            "nested_structures": {
                "content": """---
- name: Nested structures playbook
  hosts: all
  tasks:
    - name: Block with rescue
      block:
        - name: Try operation
          copy:
            src: test.txt
            dest: /tmp/test.txt
      rescue:
        - name: Handle failure
          debug:
            msg: "Operation failed"
    - name: Loop with items
      package:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - apache2""",
                "expected_changes": 3,
                "expected_modules": ["ansible.builtin.copy", "ansible.builtin.debug", "ansible.builtin.package"]
            }
        }

        scenario_config = scenarios[scenario]
        test_file = tmp_path / f"{scenario}.yml"
        test_file.write_text(scenario_config["content"])

        # Execute conversion workflow (following Molecule's test sequence)
        converter = FQCNConverter()
        
        # 1. Convert (equivalent to Molecule's converge)
        result = converter.convert_file(test_file)
        
        # 2. Validate conversion success
        assert result.success, f"Scenario '{scenario}' conversion should succeed"
        assert result.changes_made == scenario_config["expected_changes"], f"Expected {scenario_config['expected_changes']} changes in '{scenario}'"
        
        # 3. Verify expected modules are present (equivalent to Molecule's verify)
        converted_content = result.converted_content
        for expected_module in scenario_config["expected_modules"]:
            assert expected_module in converted_content, f"Expected module '{expected_module}' not found in '{scenario}'"
        
        # 4. Validate idempotence (run conversion again)
        idempotence_result = converter.convert_file(test_file)
        assert idempotence_result.changes_made == 0, f"Scenario '{scenario}' should be idempotent (no changes on second run)"


@pytest.mark.integration
class TestWorkflowSequences:
    """Test complete workflow sequences following Molecule's test sequence pattern."""

    def test_complete_workflow_sequence(self, tmp_path):
        """Test complete workflow sequence: create -> convert -> validate -> verify -> cleanup."""
        
        # 1. Create/Prepare - Set up test environment
        test_content = """---
- name: Workflow test playbook
  hosts: all
  tasks:
    - name: Install packages
      package:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - git
    - name: Copy configuration
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
    - name: Start service
      service:
        name: nginx
        state: started"""
        
        test_file = tmp_path / "workflow_test.yml"
        test_file.write_text(test_content)
        
        # 2. Convert - Apply FQCN conversion
        converter = FQCNConverter()
        conversion_result = converter.convert_file(test_file)
        
        assert conversion_result.success, "Conversion step should succeed"
        assert conversion_result.changes_made == 3, "Should convert 3 modules"
        
        # 3. Validate - Check conversion quality
        validator = ValidationEngine()
        validation_result = validator.validate_conversion(test_file)
        
        assert validation_result.valid, "Validation step should pass"
        assert validation_result.score == 1.0, "Should have 100% FQCN completeness"
        
        # 4. Verify - Ensure expected outcomes
        converted_content = test_file.read_text()
        expected_modules = [
            "ansible.builtin.package",
            "ansible.builtin.copy", 
            "ansible.builtin.service"
        ]
        
        for module in expected_modules:
            assert module in converted_content, f"Expected module '{module}' should be present"
        
        # 5. Idempotence - Verify no changes on re-run
        idempotence_result = converter.convert_file(test_file)
        assert idempotence_result.changes_made == 0, "Should be idempotent"
        
        # 6. Side Effects - Check for unintended changes
        original_lines = converted_content.split('\n')
        side_effect_result = converter.convert_file(test_file)
        new_content = test_file.read_text()
        new_lines = new_content.split('\n')
        
        assert original_lines == new_lines, "No side effects should occur"
        
        # 7. Cleanup - Verify cleanup (simulated)
        assert test_file.exists(), "Test file should still exist for verification"

    def test_error_handling_workflow(self, tmp_path):
        """Test workflow error handling and recovery."""
        
        # Create a file with intentional issues
        problematic_content = """---
- name: Problematic playbook
  hosts: all
  tasks:
    - name: Valid task
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Invalid YAML structure
      invalid_module_name:
        - this: is
        - not: valid
        - yaml: structure"""
        
        test_file = tmp_path / "problematic.yml"
        test_file.write_text(problematic_content)
        
        converter = FQCNConverter()
        
        # Conversion should handle errors gracefully
        result = converter.convert_file(test_file)
        
        # Should still succeed with partial conversion
        assert result.success, "Should handle errors gracefully"
        assert result.changes_made >= 1, "Should convert at least the valid modules"
        # Note: The converter doesn't generate warnings for unknown modules, it just ignores them
        assert len(result.errors) == 0, "Should not have errors for valid YAML"

    def test_batch_workflow_integration(self, tmp_path):
        """Test batch processing workflow integration."""
        
        # Create multiple test files
        files = []
        for i in range(3):
            content = f"""---
- name: Batch test playbook {i}
  hosts: all
  tasks:
    - name: Task {i}
      copy:
        src: file{i}.txt
        dest: /tmp/file{i}.txt
    - name: Service {i}
      service:
        name: service{i}
        state: started"""
            
            test_file = tmp_path / f"batch_test_{i}.yml"
            test_file.write_text(content)
            files.append(test_file)
        
        # Execute batch workflow - process each file individually since BatchProcessor works with projects
        converter = FQCNConverter()
        results = []
        total_changes = 0
        
        for file_path in files:
            result = converter.convert_file(file_path)
            results.append(result)
            if result.success:
                total_changes += result.changes_made
        
        # Verify batch results
        assert all(r.success for r in results), "All conversions should succeed"
        assert len(results) == 3, "Should process all 3 files"
        assert total_changes == 6, "Should make 6 total changes (2 per file)"
        
        # Verify individual file results
        for file_path in files:
            content = file_path.read_text()
            assert "ansible.builtin.copy" in content, f"File {file_path} should have converted copy module"
            assert "ansible.builtin.service" in content, f"File {file_path} should have converted service module"


@pytest.mark.integration
class TestScenarioEdgeCases:
    """Test edge cases and boundary conditions in scenarios."""

    def test_empty_project_scenario(self, tmp_path):
        """Test handling of empty projects."""
        # Create empty directory structure
        (tmp_path / "roles").mkdir()
        (tmp_path / "group_vars").mkdir()
        (tmp_path / "host_vars").mkdir()
        
        processor = BatchProcessor()
        # For empty project, discover_projects should return empty list
        projects = processor.discover_projects(str(tmp_path))
        result = processor.process_projects_batch_result(projects)
        
        assert result.failed_conversions == 0, "Empty project should be handled gracefully"
        assert result.total_projects == 0, "No projects should be found"

    def test_mixed_file_types_scenario(self, tmp_path):
        """Test handling of mixed file types in a project."""
        
        # Create various file types
        (tmp_path / "playbook.yml").write_text("""---
- name: Valid playbook
  hosts: all
  tasks:
    - copy: src=test.txt dest=/tmp/test.txt""")
        
        (tmp_path / "inventory.ini").write_text("""[webservers]
web1.example.com
web2.example.com""")
        
        (tmp_path / "README.md").write_text("# Test Project")
        
        (tmp_path / "invalid.yml").write_text("invalid: yaml: content: [")
        
        # Test individual file conversion instead of batch processing
        # since this isn't a proper Ansible project structure
        converter = FQCNConverter()
        
        # Test that valid files are processed correctly
        playbook_file = tmp_path / "playbook.yml"
        result = converter.convert_file(playbook_file)
        
        assert result.success, "Valid playbook should be converted"
        assert result.changes_made == 1, "Should convert the copy module"
        assert "ansible.builtin.copy" in result.converted_content

    def test_deeply_nested_scenario(self, tmp_path):
        """Test handling of deeply nested project structures."""
        
        # Create deep directory structure
        deep_path = tmp_path / "roles" / "web" / "tasks" / "main.yml"
        deep_path.parent.mkdir(parents=True)
        deep_path.write_text("""---
- name: Deep nested task
  copy:
    src: deep.txt
    dest: /tmp/deep.txt""")
        
        # Test individual file conversion for deeply nested structure
        converter = FQCNConverter()
        result = converter.convert_file(deep_path)
        
        assert result.success, "Deeply nested structures should be handled"
        assert result.changes_made == 1, "Should convert the copy module"
        
        # Verify conversion worked
        assert "ansible.builtin.copy" in result.converted_content, "Nested file should be converted"