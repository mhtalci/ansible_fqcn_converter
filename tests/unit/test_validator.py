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
