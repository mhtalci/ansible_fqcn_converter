"""
Validation engine for FQCN conversions.

This module provides validation functionality to ensure that Ansible playbooks
have been properly converted to use FQCNs and to identify any issues or
incomplete conversions.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Union

import yaml

from ..config.manager import ConfigurationManager
from ..exceptions import (
    FileAccessError,
    ValidationError,
    YAMLParsingError,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a file.

    This class encapsulates information about a specific validation problem,
    including its location, severity, and suggested remediation.

    Attributes:
        line_number: Line number where the issue occurs (1-based)
        column: Column number where the issue occurs (1-based)
        severity: Severity level of the issue ('error', 'warning', 'info')
        message: Human-readable description of the issue
        suggestion: Suggested fix or remediation for the issue
        module_name: Name of the module related to this issue (optional)
        expected_fqcn: Expected FQCN for the module (optional)

    Example:
        >>> issue = ValidationIssue(
        ...     line_number=15,
        ...     column=5,
        ...     severity='error',
        ...     message="Short module name 'copy' should use FQCN",
        ...     suggestion="Replace 'copy' with 'ansible.builtin.copy'"
        ... )
    """

    line_number: int
    column: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: str = ""
    module_name: str = ""
    expected_fqcn: str = ""


@dataclass
class ValidationResult:
    """
    Result of validation operation.

    This class contains comprehensive information about the validation of an
    Ansible file, including compliance score, issues found, and statistics.

    Attributes:
        valid: Whether the file passes validation (no critical errors)
        file_path: Path to the validated file
        issues: List of validation issues found in the file
        score: FQCN completeness score from 0.0 (no compliance) to 1.0 (fully compliant)
        total_modules: Total number of modules found in the file
        fqcn_modules: Number of modules already using FQCN format
        short_modules: Number of modules using short names
        processing_time: Time taken for validation in seconds

    Example:
        >>> result = validator.validate_file("playbook.yml")
        >>> print(f"Validation score: {result.score:.1%}")
        >>> if not result.valid:
        ...     for issue in result.issues:
        ...         print(f"Line {issue.line_number}: {issue.message}")
    """

    valid: bool
    file_path: str
    issues: List[ValidationIssue] = field(default_factory=list)
    score: float = 0.0  # Conversion completeness score (0.0 to 1.0)
    total_modules: int = 0
    fqcn_modules: int = 0
    short_modules: int = 0
    processing_time: float = 0.0


class ValidationEngine:
    """
    Handles validation of FQCN conversions with comprehensive validation logic.

    The ValidationEngine analyzes Ansible files to ensure proper FQCN usage,
    identifies conversion issues, and provides detailed compliance scoring.
    It supports various validation modes and provides actionable feedback.

    Features:
        - Comprehensive FQCN compliance checking
        - Detailed issue reporting with line numbers
        - Compliance scoring (0.0 to 1.0)
        - Support for multiple Ansible file formats
        - Configurable validation strictness
        - Performance metrics and timing

    Example:
        >>> validator = ValidationEngine()
        >>> result = validator.validate_file("playbook.yml")
        >>>
        >>> if result.valid:
        ...     print(f"✅ File is compliant (score: {result.score:.1%})")
        ... else:
        ...     print(f"❌ Found {len(result.issues)} issues")
        ...     for issue in result.issues:
        ...         print(f"  Line {issue.line_number}: {issue.message}")

        >>> # Validate content directly
        >>> yaml_content = "- copy: {src: file, dest: /tmp/file}"
        >>> result = validator.validate_content(yaml_content)
    """

    def __init__(self) -> None:
        """Initialize validation engine."""
        self._config_manager = ConfigurationManager()
        self._known_modules: Dict[str, str] = {}
        self._fqcn_modules: Set[str] = set()

        try:
            # Load known module mappings for validation
            self._known_modules = self._config_manager.load_default_mappings()

            # Build set of FQCN module names for validation
            self._fqcn_modules = set(self._known_modules.values())

            logger.info(
                f"Initialized validator with {len(self._known_modules)} known modules"
            )

        except Exception as e:
            logger.warning(f"Failed to load module mappings for validation: {e}")
            self._known_modules = {}
            self._fqcn_modules = set()

    def validate_conversion(self, file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate that a file has been properly converted.

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult with validation details

        Raises:
            FileAccessError: If file cannot be read
            ValidationError: If validation process fails
        """
        file_path = Path(file_path)

        result = ValidationResult(valid=True, file_path=str(file_path))

        try:
            # Read file content
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (IOError, OSError) as e:
                raise FileAccessError(
                    f"Cannot read file for validation: {file_path}", details=str(e)
                ) from e

            # Parse and validate content
            self._validate_content(content, result)

            # Calculate overall validation score
            result.score = self._calculate_completeness_score(content, result.issues)

            # Determine if validation passed
            error_count = sum(1 for issue in result.issues if issue.severity == "error")
            result.valid = error_count == 0

            logger.debug(
                f"Validation completed for {file_path}: "
                f"valid={result.valid}, score={result.score:.2f}, "
                f"issues={len(result.issues)}"
            )

            return result

        except (FileAccessError, ValidationError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            raise ValidationError(
                f"Unexpected error during validation: {file_path}", details=str(e)
            ) from e

    def validate_content(
        self, content: str, file_path: str = "<content>"
    ) -> ValidationResult:
        """
        Validate content string for FQCN compliance.

        Args:
            content: The content to validate
            file_path: Optional file path for reporting

        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(valid=True, file_path=file_path)

        self._validate_content(content, result)

        # Count modules and calculate score
        try:
            yaml_data = yaml.safe_load(content)
            if yaml_data is not None:
                total_modules, fqcn_modules, short_modules = self._count_modules(
                    yaml_data
                )
                result.total_modules = total_modules
                result.fqcn_modules = fqcn_modules
                result.short_modules = short_modules
        except Exception as e:
            logger.warning(f"Error counting modules: {e}")

        result.score = self._calculate_completeness_score(content, result.issues)

        error_count = sum(1 for issue in result.issues if issue.severity == "error")
        result.valid = error_count == 0

        return result

    def _validate_content(self, content: str, result: ValidationResult) -> None:
        """Perform validation on content and populate result with issues."""
        try:
            # Parse YAML content
            try:
                yaml_data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                result.issues.append(
                    ValidationIssue(
                        line_number=1,
                        column=1,
                        severity="error",
                        message=f"YAML parsing error: {str(e)}",
                        suggestion="Fix YAML syntax errors",
                    )
                )
                return

            if yaml_data is None:
                return

            # Split content into lines for line number tracking
            lines = content.split("\n")

            # Validate different Ansible structures
            if isinstance(yaml_data, list):
                # Playbook format (list of plays)
                self._validate_playbook(yaml_data, lines, result)
            elif isinstance(yaml_data, dict):
                # Task file or other dict-based format
                self._validate_dict_structure(yaml_data, lines, result)

        except Exception as e:
            result.issues.append(
                ValidationIssue(
                    line_number=1,
                    column=1,
                    severity="error",
                    message=f"Validation error: {str(e)}",
                    suggestion="Check file format and content",
                )
            )

    def _validate_playbook(
        self, playbook: List[Any], lines: List[str], result: ValidationResult
    ) -> None:
        """Validate playbook structure (list of plays)."""
        for play_idx, play in enumerate(playbook):
            if not isinstance(play, dict):
                continue

            # Validate tasks in different sections
            for section in ["tasks", "handlers", "pre_tasks", "post_tasks"]:
                if section in play and isinstance(play[section], list):
                    self._validate_tasks(
                        play[section], lines, result, f"play[{play_idx}].{section}"
                    )

    def _validate_dict_structure(
        self, data: Dict[str, Any], lines: List[str], result: ValidationResult
    ) -> None:
        """Validate dictionary-based structure."""
        # Check for tasks in various locations
        for section in ["tasks", "handlers", "pre_tasks", "post_tasks"]:
            if section in data and isinstance(data[section], list):
                self._validate_tasks(data[section], lines, result, section)

    def _validate_tasks(
        self, tasks: List[Any], lines: List[str], result: ValidationResult, context: str
    ) -> None:
        """Validate tasks for FQCN compliance."""
        for task_idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            # Check each key in the task
            for key, value in task.items():
                # Skip non-module keys
                if key in [
                    "name",
                    "when",
                    "tags",
                    "vars",
                    "register",
                    "delegate_to",
                    "become",
                    "become_user",
                    "ignore_errors",
                    "changed_when",
                    "failed_when",
                    "notify",
                    "listen",
                    "with_items",
                    "loop",
                    "until",
                    "retries",
                    "delay",
                    "run_once",
                    "local_action",
                ]:
                    continue

                # Find line number for this task/module
                line_number = self._find_line_number(lines, key, task_idx)

                # Check if this is a known short module name
                if key in self._known_modules:
                    fqcn = self._known_modules[key]
                    result.issues.append(
                        ValidationIssue(
                            line_number=line_number,
                            column=1,
                            severity="error",
                            message=f"Short module name '{key}' should be converted to FQCN",
                            suggestion=f"Replace '{key}' with '{fqcn}'",
                        )
                    )

                # Check if this looks like a module but isn't recognized
                elif self._looks_like_module(key) and key not in self._fqcn_modules:
                    # Check if it's already an FQCN format
                    if "." in key and not key.startswith("."):
                        # Might be a valid FQCN we don't know about
                        result.issues.append(
                            ValidationIssue(
                                line_number=line_number,
                                column=1,
                                severity="info",
                                message=f"Unknown FQCN module '{key}' - verify this is correct",
                                suggestion="Ensure this FQCN is valid and the collection is available",
                            )
                        )
                    else:
                        # Looks like a module but not in our known list
                        result.issues.append(
                            ValidationIssue(
                                line_number=line_number,
                                column=1,
                                severity="warning",
                                message=f"Unknown module '{key}' - may need FQCN conversion",
                                suggestion="Check if this module requires FQCN conversion",
                            )
                        )

    def _find_line_number(
        self, lines: List[str], module_name: str, task_index: int
    ) -> int:
        """Find the line number where a module is used."""
        # Simple heuristic to find the line number
        # Look for the module name in the lines
        for i, line in enumerate(lines):
            if module_name in line and ":" in line:
                # Check if this looks like a module usage
                stripped = line.strip()
                if stripped.startswith(module_name + ":") or stripped.startswith(
                    "- " + module_name + ":"
                ):
                    return i + 1  # Line numbers are 1-based

        # Fallback: estimate based on task index
        return max(1, task_index * 5 + 1)  # Rough estimate

    def _looks_like_module(self, key: str) -> bool:
        """Determine if a key looks like an Ansible module."""
        # Skip obvious non-module keys
        if key.startswith("_") or key in [
            "block",
            "rescue",
            "always",
            "include",
            "import_tasks",
            "include_tasks",
            "import_playbook",
            "meta",
        ]:
            return False

        # Must be a valid identifier-like string
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_.-]*$", key):
            return False

        return True

    def _count_modules(self, yaml_data: Any) -> tuple[int, int, int]:
        """Count total modules, FQCN modules, and short modules."""
        total_modules = 0
        fqcn_modules = 0
        short_modules = 0

        def count_in_structure(data: Any) -> None:
            nonlocal total_modules, fqcn_modules, short_modules

            if isinstance(data, dict):
                for key, value in data.items():
                    # Skip non-module keys
                    if key in [
                        "name",
                        "hosts",
                        "vars",
                        "tasks",
                        "handlers",
                        "pre_tasks",
                        "post_tasks",
                        "when",
                        "with_items",
                        "loop",
                        "register",
                        "tags",
                        "become",
                        "become_user",
                        "until",
                        "retries",
                        "delay",
                        "run_once",
                        "local_action",
                        "block",
                        "rescue",
                        "always",
                    ]:
                        if isinstance(value, (list, dict)):
                            count_in_structure(value)
                        continue

                    # Check if this looks like a module
                    if self._looks_like_module(key):
                        total_modules += 1
                        if "." in key and not key.startswith("."):
                            fqcn_modules += 1
                        else:
                            short_modules += 1

                    # Recursively count in nested structures
                    if isinstance(value, (list, dict)):
                        count_in_structure(value)

            elif isinstance(data, list):
                for item in data:
                    count_in_structure(item)

        count_in_structure(yaml_data)
        return total_modules, fqcn_modules, short_modules

    def _calculate_completeness_score(
        self, content: str, issues: List[ValidationIssue]
    ) -> float:
        """
        Calculate FQCN completeness score (0.0 to 1.0).

        Args:
            content: The file content
            issues: List of validation issues

        Returns:
            Score from 0.0 (no FQCN compliance) to 1.0 (fully compliant)
        """
        try:
            # Parse content to count modules
            yaml_data = yaml.safe_load(content)
            if yaml_data is None:
                return 1.0  # Empty file is considered compliant

            # Count modules in the structure
            total_modules, fqcn_modules, short_modules = self._count_modules(yaml_data)

            if total_modules == 0:
                return 1.0  # No modules found, consider compliant

            # Calculate base score based on FQCN usage
            base_score = fqcn_modules / total_modules if total_modules > 0 else 1.0

            # For now, just return the base score without penalties
            # This gives a cleaner score based purely on FQCN adoption
            return min(1.0, base_score)

        except Exception as e:
            logger.warning(f"Error calculating completeness score: {e}")
            return 0.0  # Default score when calculation fails$', key):
            return False

        return True

    def _count_modules(self, yaml_data: Any) -> tuple[int, int, int]:
        """
        Count total modules, FQCN modules, and short modules.

        Returns:
            Tuple of (total_modules, fqcn_modules, short_modules)
        """
        total_modules = 0
        fqcn_modules = 0
        short_modules = 0

        if isinstance(yaml_data, list):
            # Playbook format
            for play in yaml_data:
                if isinstance(play, dict):
                    for section in ["tasks", "handlers", "pre_tasks", "post_tasks"]:
                        if section in play and isinstance(play[section], list):
                            t, f, s = self._count_modules_in_tasks(play[section])
                            total_modules += t
                            fqcn_modules += f
                            short_modules += s

        elif isinstance(yaml_data, dict):
            # Task file format
            for section in ["tasks", "handlers", "pre_tasks", "post_tasks"]:
                if section in yaml_data and isinstance(yaml_data[section], list):
                    t, f, s = self._count_modules_in_tasks(yaml_data[section])
                    total_modules += t
                    fqcn_modules += f
                    short_modules += s

        return total_modules, fqcn_modules, short_modules

    def _count_modules_in_tasks(self, tasks: List[Any]) -> tuple[int, int, int]:
        """Count modules in a list of tasks."""
        total_modules = 0
        fqcn_modules = 0
        short_modules = 0

        for task in tasks:
            if not isinstance(task, dict):
                continue

            # Count only one module per task (the main action)
            module_found = False
            for key in task.keys():
                # Skip non-module keys
                if key in [
                    "name",
                    "when",
                    "with_items",
                    "loop",
                    "register",
                    "tags",
                    "become",
                    "become_user",
                    "until",
                    "retries",
                    "delay",
                    "run_once",
                    "local_action",
                    "block",
                    "rescue",
                    "always",
                    "vars",
                    "environment",
                    "delegate_to",
                    "connection",
                    "remote_user",
                    "port",
                    "become_method",
                    "become_flags",
                    "check_mode",
                    "diff",
                    "ignore_errors",
                    "changed_when",
                    "failed_when",
                    "no_log",
                    "throttle",
                    "timeout",
                    "any_errors_fatal",
                    "max_fail_percentage",
                ]:
                    continue

                if self._looks_like_module(key) and not module_found:
                    total_modules += 1
                    module_found = True

                    if key in self._known_modules:
                        # This is a known short module name
                        short_modules += 1
                    elif "." in key and not key.startswith("."):
                        # This looks like an FQCN
                        fqcn_modules += 1
                    elif key in self._fqcn_modules:
                        # This is a known FQCN
                        fqcn_modules += 1
                    break  # Only count one module per task

        return total_modules, fqcn_modules, short_modules
