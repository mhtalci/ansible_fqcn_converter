"""
Test utilities for FQCN Converter testing.

This module provides utilities for file system mocking, assertion helpers,
and common testing patterns.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, mock_open, patch

import yaml


class MockFileSystem:
    """Mock file system for testing without actual file I/O."""

    def __init__(self):
        self.files: Dict[str, str] = {}
        self.directories: set = set()

    def add_file(self, path: str, content: str) -> None:
        """Add a file to the mock file system."""
        self.files[path] = content
        # Add parent directories
        parent = str(Path(path).parent)
        while parent != "." and parent != "/":
            self.directories.add(parent)
            parent = str(Path(parent).parent)

    def add_directory(self, path: str) -> None:
        """Add a directory to the mock file system."""
        self.directories.add(path)

    def get_file_content(self, path: str) -> str:
        """Get file content from mock file system."""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]

    def file_exists(self, path: str) -> bool:
        """Check if file exists in mock file system."""
        return path in self.files

    def directory_exists(self, path: str) -> bool:
        """Check if directory exists in mock file system."""
        return path in self.directories

    def list_files(self, pattern: str = "*") -> List[str]:
        """List files matching pattern."""
        import fnmatch

        return [path for path in self.files.keys() if fnmatch.fnmatch(path, pattern)]

    @contextmanager
    def mock_open_context(self):
        """Context manager for mocking file operations."""

        def mock_open_func(path, mode="r", *args, **kwargs):
            if "r" in mode:
                if path not in self.files:
                    raise FileNotFoundError(f"File not found: {path}")
                return mock_open(read_data=self.files[path]).return_value
            elif "w" in mode or "a" in mode:
                mock_file = mock_open().return_value

                def write_side_effect(content):
                    if "w" in mode:
                        self.files[path] = content
                    else:  # append mode
                        self.files[path] = self.files.get(path, "") + content

                mock_file.write.side_effect = write_side_effect
                return mock_file

        with patch("builtins.open", side_effect=mock_open_func):
            yield


class TempProjectBuilder:
    """Builder for creating temporary Ansible projects for testing."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.base_dir = Path(tempfile.mkdtemp())
            self._cleanup_needed = True
        else:
            self.base_dir = base_dir
            self._cleanup_needed = False

        self.project_dir = self.base_dir / "test_project"
        self.project_dir.mkdir(exist_ok=True)

    def add_playbook(self, name: str, content: str) -> "TempProjectBuilder":
        """Add a playbook to the project."""
        playbook_file = self.project_dir / f"{name}.yml"
        playbook_file.write_text(content)
        return self

    def add_role(self, role_name: str, files: Dict[str, str]) -> "TempProjectBuilder":
        """Add a role with specified files to the project."""
        role_dir = self.project_dir / "roles" / role_name

        for file_path, content in files.items():
            full_path = role_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        return self

    def add_inventory(self, content: str) -> "TempProjectBuilder":
        """Add inventory file to the project."""
        inventory_file = self.project_dir / "inventory.ini"
        inventory_file.write_text(content)
        return self

    def add_group_vars(
        self, group: str, vars_dict: Dict[str, Any]
    ) -> "TempProjectBuilder":
        """Add group variables to the project."""
        group_vars_dir = self.project_dir / "group_vars"
        group_vars_dir.mkdir(exist_ok=True)

        vars_file = group_vars_dir / f"{group}.yml"
        vars_file.write_text(yaml.dump(vars_dict, default_flow_style=False))
        return self

    def add_host_vars(
        self, host: str, vars_dict: Dict[str, Any]
    ) -> "TempProjectBuilder":
        """Add host variables to the project."""
        host_vars_dir = self.project_dir / "host_vars"
        host_vars_dir.mkdir(exist_ok=True)

        vars_file = host_vars_dir / f"{host}.yml"
        vars_file.write_text(yaml.dump(vars_dict, default_flow_style=False))
        return self

    def add_file(self, relative_path: str, content: str) -> "TempProjectBuilder":
        """Add arbitrary file to the project."""
        file_path = self.project_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return self

    def build(self) -> Path:
        """Return the project directory path."""
        return self.project_dir

    def cleanup(self) -> None:
        """Clean up temporary directory if created by this builder."""
        if self._cleanup_needed and self.base_dir.exists():
            shutil.rmtree(self.base_dir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class AssertionHelpers:
    """Helper methods for common test assertions."""

    @staticmethod
    def assert_yaml_valid(content: str) -> None:
        """Assert that content is valid YAML."""
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise AssertionError(f"Invalid YAML content: {e}")

    @staticmethod
    def assert_contains_fqcn(content: str, module_name: str, fqcn: str) -> None:
        """Assert that content contains the expected FQCN conversion."""
        assert f"{fqcn}:" in content, f"Expected FQCN '{fqcn}:' not found in content"
        # Ensure the short name is not present (unless it's in a comment or string)
        lines = content.split("\n")
        for line in lines:
            if f"{module_name}:" in line and not line.strip().startswith("#"):
                # Check if it's actually the module usage, not a parameter
                stripped = line.strip()
                if stripped.startswith(f"- {module_name}:") or stripped.startswith(
                    f"{module_name}:"
                ):
                    raise AssertionError(
                        f"Short module name '{module_name}:' still present in: {line}"
                    )

    @staticmethod
    def assert_preserves_parameters(content: str, parameter_name: str) -> None:
        """Assert that parameter names are preserved and not converted."""
        # Parameters should appear as "parameter_name: value" not as module calls
        lines = content.split("\n")
        parameter_lines = [line for line in lines if f"{parameter_name}:" in line]

        for line in parameter_lines:
            stripped = line.strip()
            # Skip if it's a comment
            if stripped.startswith("#"):
                continue

            # Parameter usage should be indented (not a top-level module call)
            if not line.startswith("  ") and not line.startswith("\t"):
                # This might be a module call, not a parameter
                if stripped.startswith(f"- {parameter_name}:") or stripped.startswith(
                    f"{parameter_name}:"
                ):
                    continue  # This is legitimate module usage

            # Check that it's not converted to FQCN
            assert (
                f"ansible.builtin.{parameter_name}:" not in line
            ), f"Parameter '{parameter_name}' was incorrectly converted to FQCN in: {line}"

    @staticmethod
    def assert_conversion_count(content: str, expected_count: int) -> None:
        """Assert the number of FQCN conversions in content."""
        fqcn_count = content.count("ansible.builtin.")
        # Add other collection patterns as needed
        fqcn_count += content.count("community.")

        assert (
            fqcn_count >= expected_count
        ), f"Expected at least {expected_count} FQCN conversions, found {fqcn_count}"

    @staticmethod
    def assert_no_short_modules(content: str, short_modules: List[str]) -> None:
        """Assert that no short module names remain in content."""
        for module in short_modules:
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if f"{module}:" in line and not line.strip().startswith("#"):
                    stripped = line.strip()
                    if stripped.startswith(f"- {module}:") or stripped.startswith(
                        f"{module}:"
                    ):
                        raise AssertionError(
                            f"Short module name '{module}:' found on line {line_num}: {line.strip()}"
                        )

    @staticmethod
    def assert_structure_preserved(original: str, converted: str) -> None:
        """Assert that YAML structure is preserved after conversion."""
        try:
            original_data = yaml.safe_load(original)
            converted_data = yaml.safe_load(converted)
        except yaml.YAMLError as e:
            raise AssertionError(f"YAML parsing error: {e}")

        # Compare structure (this is a simplified check)
        if isinstance(original_data, list) and isinstance(converted_data, list):
            assert len(original_data) == len(
                converted_data
            ), "Number of plays changed after conversion"

        # More detailed structure comparison could be added here


class PerformanceHelpers:
    """Helpers for performance testing and benchmarking."""

    @staticmethod
    def generate_large_playbook(
        num_tasks: int, modules: Optional[List[str]] = None
    ) -> str:
        """Generate a large playbook with specified number of tasks."""
        if modules is None:
            modules = [
                "package",
                "service",
                "copy",
                "file",
                "user",
                "group",
                "command",
                "template",
            ]

        tasks = []
        for i in range(num_tasks):
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
  
  tasks:
{chr(10).join(tasks)}
"""

    @staticmethod
    def generate_complex_role_structure(
        num_roles: int, tasks_per_role: int
    ) -> Dict[str, Dict[str, str]]:
        """Generate complex role structure for performance testing."""
        roles = {}

        for i in range(num_roles):
            role_name = f"role_{i:03d}"

            # Generate tasks
            tasks = []
            for j in range(tasks_per_role):
                tasks.append(
                    f"""- name: Task {j} for {role_name}
  package:
    name: "package_{role_name}_{j}"
    state: present

- name: Service {j} for {role_name}
  service:
    name: "service_{role_name}_{j}"
    state: started"""
                )

            roles[role_name] = {
                "tasks/main.yml": f"---\n{chr(10).join(tasks)}",
                "handlers/main.yml": f"""---
- name: restart {role_name}
  service:
    name: "{role_name}"
    state: restarted""",
                "defaults/main.yml": f"""---
{role_name}_enabled: true
{role_name}_port: {8000 + i}""",
            }

        return roles

    @staticmethod
    @contextmanager
    def measure_time():
        """Context manager for measuring execution time."""
        import time

        start_time = time.time()
        yield lambda: time.time() - start_time

    @staticmethod
    @contextmanager
    def measure_memory():
        """Context manager for measuring memory usage."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss

        def get_memory_delta():
            current_memory = process.memory_info().rss
            return (current_memory - start_memory) / 1024 / 1024  # MB

        yield get_memory_delta


class ValidationHelpers:
    """Helpers for validation testing."""

    @staticmethod
    def create_validation_test_cases() -> Dict[str, Dict[str, Any]]:
        """Create test cases for validation testing."""
        return {
            "fully_converted": {
                "content": """---
- name: Fully converted
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
""",
                "expected_valid": True,
                "expected_score": 1.0,
                "expected_issues": 0,
            },
            "partially_converted": {
                "content": """---
- name: Partially converted
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
""",
                "expected_valid": False,
                "expected_score_range": (0.4, 0.6),
                "expected_issues": 1,
            },
            "not_converted": {
                "content": """---
- name: Not converted
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
""",
                "expected_valid": False,
                "expected_score": 0.0,
                "expected_issues": 2,
            },
            "unknown_modules": {
                "content": """---
- name: Unknown modules
  hosts: all
  tasks:
    - name: Known module
      ansible.builtin.copy:
        src: test.txt
        dest: /tmp/test.txt
    
    - name: Unknown module
      unknown_module:
        param: value
    
    - name: Custom collection
      custom.collection.module:
        param: value
""",
                "expected_valid": True,  # Warnings, not errors
                "expected_score_range": (0.8, 1.0),
                "expected_warnings": 2,
            },
        }

    @staticmethod
    def assert_validation_result(result, expected: Dict[str, Any]) -> None:
        """Assert validation result matches expectations."""
        if "expected_valid" in expected:
            assert (
                result.valid == expected["expected_valid"]
            ), f"Expected valid={expected['expected_valid']}, got {result.valid}"

        if "expected_score" in expected:
            assert (
                abs(result.score - expected["expected_score"]) < 0.01
            ), f"Expected score={expected['expected_score']}, got {result.score}"

        if "expected_score_range" in expected:
            min_score, max_score = expected["expected_score_range"]
            assert (
                min_score <= result.score <= max_score
            ), f"Expected score in range {expected['expected_score_range']}, got {result.score}"

        if "expected_issues" in expected:
            assert (
                len(result.issues) == expected["expected_issues"]
            ), f"Expected {expected['expected_issues']} issues, got {len(result.issues)}"

        if "expected_warnings" in expected:
            warnings = [issue for issue in result.issues if issue.severity == "warning"]
            assert (
                len(warnings) == expected["expected_warnings"]
            ), f"Expected {expected['expected_warnings']} warnings, got {len(warnings)}"


class ConfigurationHelpers:
    """Helpers for configuration testing."""

    @staticmethod
    def create_test_config(mappings: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create test configuration with optional custom mappings."""
        base_config = {
            "ansible_builtin": {
                "copy": "ansible.builtin.copy",
                "file": "ansible.builtin.file",
                "service": "ansible.builtin.service",
                "package": "ansible.builtin.package",
                "user": "ansible.builtin.user",
                "group": "ansible.builtin.group",
                "template": "ansible.builtin.template",
                "command": "ansible.builtin.command",
                "shell": "ansible.builtin.shell",
                "debug": "ansible.builtin.debug",
                "set_fact": "ansible.builtin.set_fact",
            },
            "community_general": {
                "docker_container": "community.docker.docker_container",
                "mysql_user": "community.mysql.mysql_user",
                "postgresql_user": "community.postgresql.postgresql_user",
            },
        }

        if mappings:
            base_config.update(mappings)

        return base_config

    @staticmethod
    def write_config_file(config: Dict[str, Any], file_path: Path) -> None:
        """Write configuration to YAML file."""
        with open(file_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    @staticmethod
    @contextmanager
    def temporary_config(config: Dict[str, Any]):
        """Context manager for temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config, f, default_flow_style=False)
            config_path = f.name

        try:
            yield Path(config_path)
        finally:
            os.unlink(config_path)
