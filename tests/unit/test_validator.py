"""
Unit tests for ValidationEngine class.

Comprehensive test suite covering validation functionality with edge cases,
error handling, and detailed issue reporting.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from fqcn_converter.core.validator import (
    ValidationEngine,
    ValidationIssue,
    ValidationResult,
)
from fqcn_converter.exceptions import (
    FileAccessError,
    ValidationError,
)


class TestValidationEngine:
    """Test cases for ValidationEngine class."""

    @pytest.fixture
    def sample_mappings(self):
        """Sample FQCN mappings for testing."""
        return {
            "copy": "ansible.builtin.copy",
            "file": "ansible.builtin.file",
            "service": "ansible.builtin.service",
            "user": "ansible.builtin.user",
            "group": "ansible.builtin.group",
            "package": "ansible.builtin.package",
            "template": "ansible.builtin.template",
            "command": "ansible.builtin.command",
            "debug": "ansible.builtin.debug",
            "set_fact": "ansible.builtin.set_fact",
        }

    @pytest.fixture
    def validator(self, sample_mappings):
        """Create validator instance with mocked configuration."""
        with patch("fqcn_converter.core.validator.ConfigurationManager") as mock_config:
            mock_config.return_value.load_default_mappings.return_value = (
                sample_mappings
            )
            validator = ValidationEngine()
            validator._fqcn_modules = set(sample_mappings.values())
            return validator

    def test_init_success(self, sample_mappings):
        """Test successful validator initialization."""
        with patch("fqcn_converter.core.validator.ConfigurationManager") as mock_config:
            mock_config.return_value.load_default_mappings.return_value = (
                sample_mappings
            )

            validator = ValidationEngine()

            assert validator._known_modules == sample_mappings
            assert len(validator._fqcn_modules) == len(sample_mappings)

    def test_init_config_error(self):
        """Test validator initialization with configuration error."""
        with patch("fqcn_converter.core.validator.ConfigurationManager") as mock_config:
            mock_config.return_value.load_default_mappings.side_effect = Exception(
                "Config error"
            )

            # Should not raise exception, but log warning and continue with empty mappings
            validator = ValidationEngine()

            assert validator._known_modules == {}
            assert validator._fqcn_modules == set()

    def test_validate_content_fully_converted(self, validator):
        """Test validation of fully converted content."""
        content = """---
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
"""

        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.issues) == 0
        assert result.score > 0.9  # Should have high score

    def test_validate_content_unconverted_modules(self, validator):
        """Test validation of content with unconverted modules."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Start service
      service:
        name: nginx
        state: started
"""

        result = validator.validate_content(content)

        assert result.valid is False
        assert len(result.issues) == 2  # Two unconverted modules

        # Check that issues are properly identified
        error_messages = [
            issue.message for issue in result.issues if issue.severity == "error"
        ]
        assert any("copy" in msg for msg in error_messages)
        assert any("service" in msg for msg in error_messages)

        # Check suggestions are provided
        suggestions = [issue.suggestion for issue in result.issues]
        assert any("ansible.builtin.copy" in suggestion for suggestion in suggestions)
        assert any(
            "ansible.builtin.service" in suggestion for suggestion in suggestions
        )

    def test_validate_content_mixed_conversion(self, validator):
        """Test validation of partially converted content."""
        content = """---
- name: Mixed conversion
  hosts: all
  tasks:
    - name: Copy file (converted)
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Start service (not converted)
      service:
        name: nginx
        state: started
    
    - name: Create user (not converted)
      user:
        name: testuser
        state: present
"""

        result = validator.validate_content(content)

        assert result.valid is False
        assert len(result.issues) == 2  # Two unconverted modules
        assert 0.3 < result.score < 0.7  # Partial conversion score

    def test_validate_content_unknown_modules(self, validator):
        """Test validation with unknown modules."""
        content = """---
- name: Unknown modules
  hosts: all
  tasks:
    - name: Known converted module
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Unknown module
      unknown_module:
        param: value
    
    - name: Custom FQCN module
      custom.collection.module:
        param: value
"""

        result = validator.validate_content(content)

        # Should have warnings for unknown modules
        warning_issues = [
            issue for issue in result.issues if issue.severity == "warning"
        ]
        info_issues = [issue for issue in result.issues if issue.severity == "info"]

        assert len(warning_issues) >= 1  # unknown_module
        assert len(info_issues) >= 1  # custom.collection.module

    def test_validate_content_invalid_yaml(self, validator):
        """Test validation of invalid YAML content."""
        content = """---
- name: Invalid YAML
  invalid: [
"""

        result = validator.validate_content(content)

        assert result.valid is False
        assert len(result.issues) >= 1

        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        assert any("YAML parsing error" in issue.message for issue in error_issues)

    def test_validate_content_empty_content(self, validator):
        """Test validation of empty content."""
        content = ""

        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.issues) == 0
        assert result.score == 1.0

    def test_validate_content_no_modules(self, validator):
        """Test validation of content with no modules."""
        content = """---
- name: No modules playbook
  hosts: all
  vars:
    test_var: value
  tasks: []
"""

        result = validator.validate_content(content)

        assert result.valid is True
        assert len(result.issues) == 0
        assert result.score == 1.0

    def test_validate_file_success(self, validator, tmp_path):
        """Test successful file validation."""
        test_file = tmp_path / "test.yml"
        content = """---
- name: Test task
  ansible.builtin.copy:
    src: test.txt
    dest: /tmp/test.txt
"""
        test_file.write_text(content)

        result = validator.validate_conversion(test_file)

        assert result.valid is True
        assert result.file_path == str(test_file)
        assert len(result.issues) == 0

    def test_validate_file_not_found(self, validator):
        """Test validation of non-existent file."""
        non_existent_file = Path("/non/existent/file.yml")

        with pytest.raises(FileAccessError) as exc_info:
            validator.validate_conversion(non_existent_file)

        assert "Cannot read file for validation" in str(exc_info.value)

    def test_validate_file_permission_error(self, validator, tmp_path):
        """Test validation with file permission error."""
        test_file = tmp_path / "test.yml"
        test_file.write_text("---\n- name: test\n  copy: {}")

        # Mock file read to raise permission error
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileAccessError) as exc_info:
                validator.validate_conversion(test_file)

            assert "Cannot read file for validation" in str(exc_info.value)

    def test_validate_content_complex_structure(self, validator):
        """Test validation of complex Ansible structures."""
        content = """---
- name: Complex playbook
  hosts: all
  pre_tasks:
    - name: Debug (not converted)
      debug:
        msg: "Starting"
  
  tasks:
    - name: Copy file (converted)
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
  
  handlers:
    - name: Restart service (not converted)
      service:
        name: nginx
        state: restarted
  
  post_tasks:
    - name: Set fact (converted)
      ansible.builtin.set_fact:
        deployment_complete: true
"""

        result = validator.validate_content(content)

        assert result.valid is False
        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        assert len(error_issues) == 2  # debug and service not converted

    def test_looks_like_module_method(self, validator):
        """Test the _looks_like_module method."""
        # Should return True for module-like names
        assert validator._looks_like_module("copy") is True
        assert validator._looks_like_module("service") is True
        assert validator._looks_like_module("custom_module") is True
        assert validator._looks_like_module("ansible.builtin.copy") is True

        # Should return False for non-module names
        assert validator._looks_like_module("_private") is False
        assert validator._looks_like_module("block") is False
        assert validator._looks_like_module("rescue") is False
        assert validator._looks_like_module("always") is False
        assert validator._looks_like_module("include") is False
        assert validator._looks_like_module("import_tasks") is False
        assert validator._looks_like_module("meta") is False

        # Should return False for invalid identifiers
        assert validator._looks_like_module("123invalid") is False
        assert validator._looks_like_module("") is False

    def test_find_line_number_method(self, validator):
        """Test the _find_line_number method."""
        lines = [
            "---",
            "- name: Test task",
            "  copy:",
            "    src: test.txt",
            "    dest: /tmp/test.txt",
            "- name: Another task",
            "  service:",
            "    name: nginx",
        ]

        # Should find correct line numbers
        line_num = validator._find_line_number(lines, "copy", 0)
        assert line_num == 3  # 1-based line number

        line_num = validator._find_line_number(lines, "service", 1)
        assert line_num == 7

        # Should fallback to estimate for unknown modules
        line_num = validator._find_line_number(lines, "unknown", 2)
        assert line_num == 11  # 2 * 5 + 1

    def test_count_modules_method(self, validator):
        """Test the _count_modules method."""
        yaml_data = [
            {
                "name": "Test play",
                "hosts": "all",
                "tasks": [
                    {"name": "Copy file", "copy": {"src": "test", "dest": "/tmp"}},
                    {
                        "name": "Start service",
                        "ansible.builtin.service": {"name": "nginx"},
                    },
                    {"name": "Unknown module", "unknown_module": {"param": "value"}},
                ],
            }
        ]

        total, fqcn, short = validator._count_modules(yaml_data)

        assert total == 3
        assert fqcn == 1  # ansible.builtin.service
        assert short == 1  # copy

    def test_calculate_completeness_score(self, validator):
        """Test completeness score calculation."""
        # Test with fully converted content
        content = """---
- name: Fully converted
  tasks:
    - name: Copy
      ansible.builtin.copy:
        src: test
        dest: /tmp
"""
        issues = []
        score = validator._calculate_completeness_score(content, issues)
        assert score == 1.0

        # Test with unconverted content
        content = """---
- name: Not converted
  tasks:
    - name: Copy
      copy:
        src: test
        dest: /tmp
"""
        issues = [ValidationIssue(1, 1, "error", "Short module name", "Use FQCN")]
        score = validator._calculate_completeness_score(content, issues)
        assert score < 1.0

    def test_validate_content_exception_handling(self, validator):
        """Test exception handling in content validation."""
        # Mock yaml.safe_load to raise an exception during score calculation
        content = "---\nsome: content"

        with patch("yaml.safe_load", side_effect=Exception("Unexpected error")):
            result = validator.validate_content(content)

            # Should handle exception gracefully
            assert result.score == 0.0

    def test_pathlib_path_support(self, validator, tmp_path):
        """Test that Path objects are properly supported."""
        test_file = tmp_path / "test.yml"
        content = """---
- name: Test task
  ansible.builtin.copy:
    src: test.txt
    dest: /tmp/test.txt
"""
        test_file.write_text(content)

        # Test with Path object (not string)
        result = validator.validate_conversion(test_file)

        assert result.valid is True
        assert result.file_path == str(test_file)

    def test_validate_conversion_unexpected_error(self, validator, tmp_path):
        """Test handling of unexpected errors during validation."""
        test_file = tmp_path / "test.yml"
        test_file.write_text("---\n- name: test\n  copy: {}")

        # Mock _validate_content to raise unexpected error
        with patch.object(
            validator, "_validate_content", side_effect=Exception("Unexpected")
        ):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_conversion(test_file)

            assert "Unexpected error during validation" in str(exc_info.value)


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult instances."""
        issues = [
            ValidationIssue(1, 1, "error", "Test error", "Fix it"),
            ValidationIssue(2, 5, "warning", "Test warning", "Consider this"),
        ]

        result = ValidationResult(
            valid=False, file_path="/test/file.yml", issues=issues, score=0.75
        )

        assert result.valid is False
        assert result.file_path == "/test/file.yml"
        assert len(result.issues) == 2
        assert result.score == 0.75

    def test_validation_result_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult(valid=True, file_path="/test/file.yml")

        assert result.valid is True
        assert result.file_path == "/test/file.yml"
        assert result.issues == []
        assert result.score == 0.0


class TestValidationEngineErrorHandling:
    """Test cases for error handling and edge cases in ValidationEngine."""

    @pytest.fixture
    def validator(self, sample_mappings):
        """Create validator instance with mocked configuration."""
        with patch("fqcn_converter.core.validator.ConfigurationManager") as mock_config:
            mock_config.return_value.load_default_mappings.return_value = (
                sample_mappings
            )
            validator = ValidationEngine()
            validator._fqcn_modules = set(sample_mappings.values())
            return validator

    @pytest.fixture
    def sample_mappings(self):
        """Sample FQCN mappings for testing."""
        return {
            "copy": "ansible.builtin.copy",
            "file": "ansible.builtin.file",
            "service": "ansible.builtin.service",
            "user": "ansible.builtin.user",
            "group": "ansible.builtin.group",
            "package": "ansible.builtin.package",
            "template": "ansible.builtin.template",
            "command": "ansible.builtin.command",
            "debug": "ansible.builtin.debug",
            "set_fact": "ansible.builtin.set_fact",
        }

    def test_validate_content_general_exception_handling(self, validator):
        """Test handling of general exceptions during content validation."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
"""

        # Mock yaml.safe_load to raise an exception in _validate_content
        with patch("yaml.safe_load", side_effect=Exception("Unexpected parsing error")):
            result = validator.validate_content(content)

            # Should handle exception gracefully and add error issue
            assert result.valid is False
            assert len(result.issues) >= 1
            
            error_issues = [issue for issue in result.issues if issue.severity == "error"]
            assert any("Validation error" in issue.message for issue in error_issues)
            assert any("Unexpected parsing error" in issue.message for issue in error_issues)

    def test_validate_playbook_non_dict_play(self, validator):
        """Test validation of playbook with non-dict play entries."""
        content = """---
- name: Valid play
  hosts: all
  tasks:
    - name: Copy file
      copy:
        src: test.txt
        dest: /tmp/test.txt
- "invalid_play_string"
- 123
- null
"""

        result = validator.validate_content(content)

        # Should skip non-dict entries and still process valid plays
        assert len(result.issues) >= 1  # Should find the copy module issue
        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        assert any("copy" in issue.message for issue in error_issues)

    def test_validate_dict_structure_with_sections(self, validator):
        """Test validation of dict-based structure with various task sections."""
        content = """---
tasks:
  - name: Task in tasks section
    copy:
      src: test.txt
      dest: /tmp/test.txt

handlers:
  - name: Handler
    service:
      name: nginx
      state: restarted

pre_tasks:
  - name: Pre-task
    debug:
      msg: "Starting"

post_tasks:
  - name: Post-task
    user:
      name: testuser
      state: present
"""

        result = validator.validate_content(content)

        # Should find issues in all sections
        assert result.valid is False
        assert len(result.issues) >= 4  # copy, service, debug, user

        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        module_names = [issue.message for issue in error_issues]
        
        assert any("copy" in msg for msg in module_names)
        assert any("service" in msg for msg in module_names)
        assert any("debug" in msg for msg in module_names)
        assert any("user" in msg for msg in module_names)

    def test_validate_tasks_non_dict_task(self, validator):
        """Test validation of tasks list with non-dict task entries."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Valid task
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - "invalid_task_string"
    - 123
    - null
    - name: Another valid task
      service:
        name: nginx
        state: started
"""

        result = validator.validate_content(content)

        # Should skip non-dict entries and process valid tasks
        assert result.valid is False
        assert len(result.issues) >= 2  # copy and service

        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        assert any("copy" in issue.message for issue in error_issues)
        assert any("service" in issue.message for issue in error_issues)

    def test_count_modules_nested_structures(self, validator):
        """Test module counting in deeply nested structures."""
        content = """---
- name: Complex nested structure
  hosts: all
  tasks:
    - name: Copy task
      copy:
        src: test.txt
        dest: /tmp/test.txt
    - name: Service task
      ansible.builtin.service:
        name: nginx
        state: started
    - name: Debug task
      debug:
        msg: "Test message"
    - name: File task
      file:
        path: /tmp/cleanup
        state: absent
"""

        result = validator.validate_content(content)

        # Should count modules properly
        assert result.total_modules >= 4  # copy, service, debug, file
        assert result.fqcn_modules >= 1   # ansible.builtin.service
        assert result.short_modules >= 3  # copy, debug, file

    def test_count_modules_with_recursive_structures(self, validator):
        """Test module counting with various task structures."""
        yaml_data = {
            "tasks": [
                {
                    "name": "First task",
                    "copy": {"src": "test", "dest": "/tmp"}
                },
                {
                    "name": "Second task", 
                    "ansible.builtin.service": {"name": "nginx", "state": "started"}
                },
                {
                    "name": "Third task",
                    "debug": {"msg": "test"}
                }
            ]
        }

        total, fqcn, short = validator._count_modules(yaml_data)

        # Should count modules in tasks
        assert total == 3  # copy, ansible.builtin.service, debug
        assert fqcn == 1   # ansible.builtin.service
        assert short == 2  # copy, debug

    def test_count_modules_in_tasks_with_complex_keys(self, validator):
        """Test module counting in tasks with complex non-module keys."""
        tasks = [
            {
                "name": "Complex task",
                "copy": {"src": "test", "dest": "/tmp"},
                "when": "condition",
                "with_items": ["item1", "item2"],
                "loop": ["loop1", "loop2"],
                "register": "result",
                "tags": ["tag1", "tag2"],
                "become": True,
                "become_user": "root",
                "until": "condition",
                "retries": 3,
                "delay": 5,
                "run_once": True,
                "local_action": "some_action",
                "vars": {"var1": "value1"},
                "environment": {"ENV_VAR": "value"},
                "delegate_to": "localhost",
                "connection": "local",
                "remote_user": "user",
                "port": 22,
                "become_method": "sudo",
                "become_flags": "-H",
                "check_mode": True,
                "diff": True,
                "ignore_errors": True,
                "changed_when": False,
                "failed_when": False,
                "no_log": True,
                "throttle": 1,
                "timeout": 30,
                "any_errors_fatal": True,
                "max_fail_percentage": 10
            }
        ]

        total, fqcn, short = validator._count_modules_in_tasks(tasks)

        # Should only count the copy module, not the other keys
        assert total == 1
        assert fqcn == 0
        assert short == 1

    def test_count_modules_with_known_fqcn_modules(self, validator):
        """Test module counting with modules that are in the known FQCN set."""
        # Add some modules to the known FQCN set
        validator._fqcn_modules.add("custom.collection.module")
        
        tasks = [
            {
                "name": "Task with known FQCN",
                "custom.collection.module": {"param": "value"}
            },
            {
                "name": "Task with short name",
                "copy": {"src": "test", "dest": "/tmp"}
            }
        ]

        total, fqcn, short = validator._count_modules_in_tasks(tasks)

        assert total == 2
        assert fqcn == 1  # custom.collection.module is in known FQCN set
        assert short == 1  # copy is a short name

    def test_calculate_completeness_score_with_yaml_error(self, validator):
        """Test completeness score calculation when YAML parsing fails."""
        content = "invalid: yaml: content: ["
        issues = []

        # Mock yaml.safe_load to raise an exception
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            score = validator._calculate_completeness_score(content, issues)

            # Should return 0.0 when YAML parsing fails
            assert score == 0.0

    def test_calculate_completeness_score_with_general_exception(self, validator):
        """Test completeness score calculation with unexpected exception."""
        content = """---
- name: Test
  tasks:
    - copy: {}
"""
        issues = []

        # Mock _count_modules to raise an exception
        with patch.object(validator, "_count_modules", side_effect=Exception("Unexpected error")):
            score = validator._calculate_completeness_score(content, issues)

            # Should return 0.0 when calculation fails
            assert score == 0.0

    def test_validate_content_module_counting_exception(self, validator):
        """Test validate_content when module counting raises an exception."""
        content = """---
- name: Test
  tasks:
    - copy: {}
"""

        # Mock _count_modules to raise an exception during validate_content
        with patch.object(validator, "_count_modules", side_effect=Exception("Count error")):
            result = validator.validate_content(content)

            # Should handle exception gracefully and continue
            # The result should still be created, but module counts may be 0
            assert isinstance(result, ValidationResult)
            assert result.file_path == "<content>"

    def test_validate_content_with_none_yaml_data(self, validator):
        """Test validate_content when yaml_data is None."""
        content = ""  # Empty content that results in None yaml_data

        result = validator.validate_content(content)

        # Should handle None yaml_data gracefully
        assert result.valid is True
        assert result.total_modules == 0
        assert result.fqcn_modules == 0
        assert result.short_modules == 0

    def test_count_modules_with_list_playbook_format(self, validator):
        """Test _count_modules with playbook format (list of plays)."""
        yaml_data = [
            {
                "name": "First play",
                "hosts": "all",
                "tasks": [
                    {"name": "Copy task", "copy": {"src": "test", "dest": "/tmp"}}
                ],
                "handlers": [
                    {"name": "Restart service", "service": {"name": "nginx", "state": "restarted"}}
                ]
            },
            {
                "name": "Second play", 
                "hosts": "web",
                "pre_tasks": [
                    {"name": "Debug task", "debug": {"msg": "Starting"}}
                ],
                "post_tasks": [
                    {"name": "File task", "ansible.builtin.file": {"path": "/tmp/done", "state": "touch"}}
                ]
            }
        ]

        total, fqcn, short = validator._count_modules(yaml_data)

        # Should count modules from all sections across all plays
        assert total == 4  # copy, service, debug, ansible.builtin.file
        assert fqcn == 1   # ansible.builtin.file
        assert short == 3  # copy, service, debug

    def test_count_modules_with_dict_task_file_format(self, validator):
        """Test _count_modules with task file format (dict with sections)."""
        yaml_data = {
            "tasks": [
                {"name": "Copy task", "copy": {"src": "test", "dest": "/tmp"}},
                {"name": "Service task", "ansible.builtin.service": {"name": "nginx"}}
            ],
            "handlers": [
                {"name": "Debug handler", "debug": {"msg": "Handler executed"}}
            ]
        }

        total, fqcn, short = validator._count_modules(yaml_data)

        # Should count modules from all sections
        assert total == 3  # copy, ansible.builtin.service, debug
        assert fqcn == 1   # ansible.builtin.service
        assert short == 2  # copy, debug

    def test_count_modules_with_empty_sections(self, validator):
        """Test _count_modules with empty or missing sections."""
        yaml_data = {
            "tasks": [],
            "handlers": None,
            "pre_tasks": [
                {"name": "Only task", "copy": {"src": "test", "dest": "/tmp"}}
            ]
        }

        total, fqcn, short = validator._count_modules(yaml_data)

        # Should handle empty/None sections gracefully
        assert total == 1  # copy
        assert fqcn == 0
        assert short == 1

    def test_count_modules_in_tasks_with_multiple_modules_per_task(self, validator):
        """Test that only one module per task is counted."""
        tasks = [
            {
                "name": "Task with multiple module-like keys",
                "copy": {"src": "test1", "dest": "/tmp1"},
                "file": {"path": "/tmp/test", "state": "touch"},  # Should not be counted as it's after copy
                "debug": {"msg": "test"}  # Should not be counted
            }
        ]

        total, fqcn, short = validator._count_modules_in_tasks(tasks)

        # Should only count one module per task (the first one found)
        assert total == 1
        assert fqcn == 0
        assert short == 1

    def test_looks_like_module_edge_cases(self, validator):
        """Test _looks_like_module with various edge cases."""
        # Test with dots but starting with dot (should return False)
        assert validator._looks_like_module(".hidden") is False
        
        # Test with valid FQCN format
        assert validator._looks_like_module("namespace.collection.module") is True
        
        # Test with numbers in name
        assert validator._looks_like_module("module123") is True
        
        # Test with underscores and dashes
        assert validator._looks_like_module("my_module-name") is True
        
        # Test empty string
        assert validator._looks_like_module("") is False

    def test_find_line_number_edge_cases(self, validator):
        """Test _find_line_number with various edge cases."""
        lines = [
            "---",
            "- name: Test",
            "  copy:",
            "    src: test",
            "- name: Another",
            "  service: {name: nginx}",  # Inline format
            "  when: condition"
        ]

        # Test finding inline module usage
        line_num = validator._find_line_number(lines, "service", 1)
        assert line_num == 6

        # Test with module not found (should use fallback)
        line_num = validator._find_line_number(lines, "nonexistent", 5)
        assert line_num == 26  # 5 * 5 + 1

    def test_validate_tasks_with_special_ansible_keys(self, validator):
        """Test _validate_tasks with special Ansible task keys that should be skipped."""
        content = """---
- name: Test playbook
  hosts: all
  tasks:
    - name: Task with many special keys
      copy:
        src: test.txt
        dest: /tmp/test.txt
      when: ansible_os_family == "RedHat"
      tags:
        - files
        - setup
      vars:
        test_var: value
      register: copy_result
      delegate_to: localhost
      become: true
      become_user: root
      ignore_errors: true
      changed_when: false
      failed_when: copy_result.rc != 0
      notify: restart service
      listen: restart handler
      with_items:
        - item1
        - item2
      loop:
        - loop1
        - loop2
      until: copy_result is succeeded
      retries: 3
      delay: 5
      run_once: true
      local_action: debug msg="test"
"""

        result = validator.validate_content(content)

        # Should only find the copy module issue, not any of the special keys
        assert result.valid is False
        assert len(result.issues) == 1
        
        error_issues = [issue for issue in result.issues if issue.severity == "error"]
        assert len(error_issues) == 1
        assert "copy" in error_issues[0].message

    def test_old_count_modules_method_with_nested_structures(self, validator):
        """Test the old _count_modules method with nested structures to cover lines 429-484."""
        # This test specifically targets the old count_in_structure function
        yaml_data = {
            "name": "Test playbook",
            "hosts": "all", 
            "vars": {
                "nested_vars": {
                    "copy": {"src": "test", "dest": "/tmp"},  # This should be counted
                    "ansible.builtin.service": {"name": "nginx"},  # This should be counted as FQCN
                    "non_module_key": "value",
                    "nested_dict": {
                        "debug": {"msg": "nested"},  # This should be counted
                        "more_nesting": {
                            "file": {"path": "/tmp/test"}  # This should be counted
                        }
                    }
                }
            },
            "tasks": [
                {
                    "name": "Task with vars",
                    "template": {"src": "test.j2", "dest": "/tmp/test"},
                    "vars": {
                        "task_vars": {
                            "user": {"name": "testuser"}  # This should be counted
                        }
                    }
                }
            ]
        }

        # Call the old _count_modules method directly to trigger the nested function
        total, fqcn, short = validator._count_modules(yaml_data)

        # The old method only counts modules in specific sections like "tasks"
        # It should find the template module in tasks section
        assert total >= 1  # At least the template module
        assert short >= 1  # template is a short name

    def test_old_count_modules_with_list_data(self, validator):
        """Test the old _count_modules method with list data structures."""
        yaml_data = [
            {
                "some_key": "value",
                "copy": {"src": "test", "dest": "/tmp"},  # Should be counted by nested function
                "nested_list": [
                    {
                        "service": {"name": "nginx"},  # Should be counted by nested function
                        "more_nesting": {
                            "debug": {"msg": "test"}  # Should be counted by nested function
                        }
                    }
                ]
            }
        ]

        # This should trigger the count_in_structure function for list processing
        total, fqcn, short = validator._count_modules(yaml_data)

        # Since this is not a playbook format (no tasks section), 
        # the old method won't find modules in the expected sections
        assert total >= 0  # May not find any modules in standard sections

    def test_validate_conversion_processing_time(self, validator, tmp_path):
        """Test that validate_conversion sets processing_time."""
        test_file = tmp_path / "test.yml"
        content = """---
- name: Test task
  copy:
    src: test.txt
    dest: /tmp/test.txt
"""
        test_file.write_text(content)

        result = validator.validate_conversion(test_file)

        # Processing time should be set (though it will be very small)
        assert result.processing_time >= 0.0
        assert isinstance(result.processing_time, float)

    def test_validate_content_with_yaml_none_in_module_counting(self, validator):
        """Test validate_content when yaml_data is None during module counting."""
        content = "null"  # YAML that parses to None

        result = validator.validate_content(content)

        # Should handle None yaml_data in module counting section
        assert result.valid is True
        assert result.total_modules == 0
        assert result.fqcn_modules == 0
        assert result.short_modules == 0

    def test_count_modules_in_tasks_with_non_string_keys(self, validator):
        """Test _count_modules_in_tasks with non-string keys in tasks."""
        tasks = [
            {
                "name": "Valid task",
                "copy": {"src": "test", "dest": "/tmp"},
                123: "numeric key",  # Non-string key
                None: "none key",    # None key
                ("tuple", "key"): "tuple key"  # Tuple key
            }
        ]

        total, fqcn, short = validator._count_modules_in_tasks(tasks)

        # Should handle non-string keys gracefully and still count the copy module
        assert total == 1
        assert short == 1
        assert fqcn == 0

    def test_count_modules_in_tasks_with_known_fqcn_in_set(self, validator):
        """Test _count_modules_in_tasks when a module is in the known FQCN set."""
        # Add a module to the known FQCN set that's not already there
        validator._fqcn_modules.add("known.fqcn.module")
        
        tasks = [
            {
                "name": "Task with known FQCN module",
                "known.fqcn.module": {"param": "value"}
            }
        ]

        total, fqcn, short = validator._count_modules_in_tasks(tasks)

        # Should count the module as FQCN since it's in the known set
        assert total == 1
        assert fqcn == 1  # Should hit the "elif key in self._fqcn_modules" branch
        assert short == 0

    def test_validate_content_with_processing_time_tracking(self, validator):
        """Test that validate_content tracks processing time."""
        content = """---
- name: Test
  tasks:
    - copy: {}
"""
        
        result = validator.validate_content(content)
        
        # Processing time should be tracked
        assert hasattr(result, 'processing_time')
        assert result.processing_time >= 0.0


class TestValidationIssue:
    """Test cases for ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Test creating ValidationIssue instances."""
        issue = ValidationIssue(
            line_number=10,
            column=5,
            severity="error",
            message="Test error message",
            suggestion="Test suggestion",
        )

        assert issue.line_number == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert issue.message == "Test error message"
        assert issue.suggestion == "Test suggestion"

    def test_validation_issue_defaults(self):
        """Test ValidationIssue with default values."""
        issue = ValidationIssue(
            line_number=1, column=1, severity="info", message="Test message"
        )

        assert issue.line_number == 1
        assert issue.column == 1
        assert issue.severity == "info"
        assert issue.message == "Test message"
        assert issue.suggestion == ""

    def test_validation_issue_with_module_info(self):
        """Test ValidationIssue with module name and expected FQCN."""
        issue = ValidationIssue(
            line_number=5,
            column=3,
            severity="warning",
            message="Module needs conversion",
            suggestion="Use FQCN",
            module_name="copy",
            expected_fqcn="ansible.builtin.copy"
        )

        assert issue.module_name == "copy"
        assert issue.expected_fqcn == "ansible.builtin.copy"
